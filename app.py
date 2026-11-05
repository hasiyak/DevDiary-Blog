import os
import re
import sqlite3
from functools import wraps

from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-change-me"),
        DATABASE=os.path.join(app.instance_path, "devdiary.db"),
        ADMIN_USERNAME=os.getenv("ADMIN_USERNAME", "admin"),
        ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD", "admin123"),
    )

    if test_config is not None:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    def close_db(e=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db():
        db = get_db()
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );
            """
        )
        db.commit()

    def ensure_default_admin():
        db = get_db()
        existing = db.execute(
            "SELECT id FROM admins WHERE username = ?", (app.config["ADMIN_USERNAME"],)
        ).fetchone()
        if existing is None:
            db.execute(
                "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
                (
                    app.config["ADMIN_USERNAME"],
                    generate_password_hash(app.config["ADMIN_PASSWORD"]),
                ),
            )
            db.commit()

    def slugify(text):
        slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
        return slug or "untitled-post"

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("admin_id"):
                return redirect(url_for("admin_login"))
            return view(*args, **kwargs)

        return wrapped

    @app.teardown_appcontext
    def teardown_db(exception=None):
        close_db(exception)

    @app.route("/")
    def index():
        posts = get_db().execute(
            "SELECT id, title, slug, content, created_at FROM posts ORDER BY created_at DESC"
        ).fetchall()
        return render_template("index.html", posts=posts)

    @app.route("/post/<slug>")
    def post_detail(slug):
        post = get_db().execute(
            "SELECT id, title, slug, content, created_at, updated_at FROM posts WHERE slug = ?",
            (slug,),
        ).fetchone()
        if post is None:
            abort(404)
        return render_template("post_detail.html", post=post)

    @app.route("/subscribe", methods=["POST"])
    def subscribe():
        email = (request.form.get("email") or "").strip()
        if not EMAIL_RE.match(email):
            return jsonify({"success": False, "message": "Please provide a valid email address."}), 400
        try:
            db = get_db()
            db.execute("INSERT INTO subscribers (email) VALUES (?)", (email,))
            db.commit()
        except sqlite3.IntegrityError:
            return jsonify({"success": False, "message": "Email already subscribed."}), 409
        return jsonify({"success": True, "message": "Thanks for subscribing!"})

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            admin = get_db().execute(
                "SELECT id, username, password_hash FROM admins WHERE username = ?", (username,)
            ).fetchone()
            if admin and check_password_hash(admin["password_hash"], password):
                session.clear()
                session["admin_id"] = admin["id"]
                session["admin_username"] = admin["username"]
                return redirect(url_for("admin_dashboard"))
            flash("Invalid username or password.", "danger")
        return render_template("admin/login.html")

    @app.route("/admin/logout", methods=["POST"])
    @login_required
    def admin_logout():
        session.clear()
        return redirect(url_for("index"))

    @app.route("/admin")
    @login_required
    def admin_dashboard():
        posts = get_db().execute(
            "SELECT id, title, slug, created_at, updated_at FROM posts ORDER BY created_at DESC"
        ).fetchall()
        return render_template("admin/dashboard.html", posts=posts)

    @app.route("/admin/posts/new", methods=["GET", "POST"])
    @login_required
    def admin_new_post():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            content = request.form.get("content", "").strip()
            slug = request.form.get("slug", "").strip() or slugify(title)
            if not title or not content:
                flash("Title and content are required.", "danger")
                return render_template("admin/edit_post.html", post=None)
            try:
                db = get_db()
                db.execute(
                    "INSERT INTO posts (title, slug, content) VALUES (?, ?, ?)",
                    (title, slug, content),
                )
                db.commit()
            except sqlite3.IntegrityError:
                flash("Slug already exists. Please choose another one.", "danger")
                return render_template("admin/edit_post.html", post=None)
            return redirect(url_for("admin_dashboard"))
        return render_template("admin/edit_post.html", post=None)

    @app.route("/admin/posts/<int:post_id>/edit", methods=["GET", "POST"])
    @login_required
    def admin_edit_post(post_id):
        db = get_db()
        post = db.execute(
            "SELECT id, title, slug, content FROM posts WHERE id = ?",
            (post_id,),
        ).fetchone()
        if post is None:
            abort(404)
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            content = request.form.get("content", "").strip()
            slug = request.form.get("slug", "").strip() or slugify(title)
            if not title or not content:
                flash("Title and content are required.", "danger")
                return render_template("admin/edit_post.html", post=post)
            try:
                db.execute(
                    """
                    UPDATE posts
                    SET title = ?, slug = ?, content = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (title, slug, content, post_id),
                )
                db.commit()
            except sqlite3.IntegrityError:
                flash("Slug already exists. Please choose another one.", "danger")
                return render_template("admin/edit_post.html", post=post)
            return redirect(url_for("admin_dashboard"))
        return render_template("admin/edit_post.html", post=post)

    @app.route("/admin/posts/<int:post_id>/delete", methods=["POST"])
    @login_required
    def admin_delete_post(post_id):
        db = get_db()
        db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        db.commit()
        return redirect(url_for("admin_dashboard"))

    with app.app_context():
        init_db()
        ensure_default_admin()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
