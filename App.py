import os
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session   
from werkzeug.utils import secure_filename
import pymysql

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'devdiary_admin_secure_key_2026')

# Upload configuration for post images
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'assets', 'images', 'posts')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# MySQL Database Connection configuration (Reads environment variables on cloud hosts, falls back to localhost)
db_config = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''), 
    'database': os.environ.get('DB_NAME', 'devdiary_db'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**db_config)


# Authentication decorator to protect admin routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash("Please sign in to access the admin panel.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# PUBLIC FRONTEND ROUTES
# ==========================================

@app.route('/')
def index():
    posts = []
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Fetch latest 3 articles from posts table in descending order
            sql = "SELECT * FROM posts ORDER BY id DESC LIMIT 3"
            cursor.execute(sql)
            posts = cursor.fetchall()
    except Exception as e:
        print(f"Database Error (Index Page): {e}")
        posts = []
    finally:
        if connection:
            connection.close()

    return render_template('index.html', posts=posts)


@app.route('/subscribe', methods=['POST'])
def subscribe():
    # Retrieve JSON data sent from frontend
    data = request.get_json()
    email = data.get('email') if data else None

    # Validate email address
    if not email:
        return jsonify({'success': False, 'message': 'Please enter a valid email address!'})

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Check if email is already subscribed
            cursor.execute("SELECT id FROM subscribers WHERE email = %s", (email,))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': 'You are already subscribed!'})
            
            # Insert new subscriber into database
            cursor.execute("INSERT INTO subscribers (email) VALUES (%s)", (email,))
            connection.commit()
            
            return jsonify({'success': True, 'message': 'Thank you for subscribing to DevDiary!'})
    except Exception as e:
        print(f"Newsletter Error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred. Please try again later.'})
    finally:
        if connection:
            connection.close()


@app.route('/blog')
def blog():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')
    search_query = request.args.get('q')
    
    per_page = 4
    offset = (page - 1) * per_page

    posts = []
    categories = []
    total_pages = 0
    connection = None

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Base Queries for pagination and data retrieval
            count_sql = "SELECT COUNT(*) AS total FROM posts WHERE 1=1"
            data_sql = "SELECT * FROM posts WHERE 1=1"
            params = []

            # Filter by category if provided
            if category:
                count_sql += " AND category = %s"
                data_sql += " AND category = %s"
                params.append(category)

            # Filter by search query if provided
            if search_query:
                count_sql += " AND title LIKE %s"
                data_sql += " AND title LIKE %s"
                params.append(f"%{search_query}%")

            cursor.execute(count_sql, tuple(params))
            result = cursor.fetchone()
            total_posts = result['total'] if result else 0
            total_pages = (total_posts + per_page - 1) // per_page

            data_sql += " ORDER BY id DESC LIMIT %s OFFSET %s"
            data_params = params.copy()
            data_params.extend([per_page, offset])
            
            cursor.execute(data_sql, tuple(data_params))
            posts = cursor.fetchall()

            # Retrieve distinct categories with article count
            category_sql = """
                SELECT category, COUNT(*) as post_count 
                FROM posts 
                GROUP BY category 
                ORDER BY post_count DESC
            """
            cursor.execute(category_sql)
            categories = cursor.fetchall()
            
    except Exception as e:
        print(f"Database Error (Blog Page): {e}")
        posts = []
        total_pages = 0
    finally:
        if connection:
            connection.close()

    return render_template('blog.html', posts=posts, page=page, total_pages=total_pages, category=category, search_query=search_query, categories=categories)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    success_msg = None
    error_msg = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not message:
            error_msg = "Please fill in all required fields."
        else:
            connection = None
            try:
                connection = get_db_connection()
                with connection.cursor() as cursor:
                    sql = "INSERT INTO messages (name, email, subject, message) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql, (name, email, subject, message))
                connection.commit()
                success_msg = "Your message has been sent successfully!"
            except Exception as e:
                print(f"Database Error (Contact Page): {e}")
                error_msg = "Message could not be sent. Please try again later."
            finally:
                if connection:
                    connection.close()

    return render_template('contact.html', success_msg=success_msg, error_msg=error_msg)


@app.route('/post/<int:id>', methods=['GET', 'POST'])
def single_post(id):
    success_msg = None
    error_msg = None
    post = None
    comments = []
    categories = []
    connection = None
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Handle comment submission
            if request.method == 'POST':
                name = request.form.get('name', '').strip()
                email = request.form.get('email', '').strip()
                comment = request.form.get('comment', '').strip()

                if not name or not email or not comment:
                    error_msg = "Please provide your name, email, and comment."
                else:
                    sql_insert = "INSERT INTO comments (post_id, name, email, comment) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql_insert, (id, name, email, comment))
                    connection.commit()
                    success_msg = "Your comment has been posted successfully!"

            # Fetch post data
            sql_post = "SELECT * FROM posts WHERE id = %s"
            cursor.execute(sql_post, (id,))
            post = cursor.fetchone()
            
            # Fetch comments for this specific post
            sql_comments = "SELECT * FROM comments WHERE post_id = %s ORDER BY id DESC"
            cursor.execute(sql_comments, (id,))
            comments = cursor.fetchall()
            
            # Fetch categories summary
            category_sql = """
                SELECT category, COUNT(*) as post_count 
                FROM posts 
                GROUP BY category 
                ORDER BY post_count DESC
            """
            cursor.execute(category_sql)
            categories = cursor.fetchall()
            
    except Exception as e:
        print(f"Database Error (Single Post ID {id}): {e}")
        post = None
        comments = []
    finally:
        if connection:
            connection.close()

    status_code = 200 if post is not None else 404
    return render_template('single-post.html', post=post, comments=comments, success_msg=success_msg, error_msg=error_msg, categories=categories), status_code


@app.route('/post/<int:id>/like', methods=['POST'])
def like_post(id):
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, likes FROM posts WHERE id = %s", (id,))
            post = cursor.fetchone()
            if not post:
                return jsonify({'success': False, 'message': 'Post not found'}), 404

            cursor.execute("UPDATE posts SET likes = COALESCE(likes, 0) + 1 WHERE id = %s", (id,))
            connection.commit()
            
            cursor.execute("SELECT likes FROM posts WHERE id = %s", (id,))
            result = cursor.fetchone()
            new_likes = result['likes'] if result else 0
            
            return jsonify({'success': True, 'likes': new_likes})
    except Exception as e:
        print(f"Error updating likes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if connection:
            connection.close()


@app.route('/api/search')
def search_suggestions():
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT id, title FROM posts WHERE title LIKE %s ORDER BY id DESC LIMIT 5"
            cursor.execute(sql, (f"%{query}%",))
            results = cursor.fetchall()
            return jsonify(results or [])
    except Exception as e:
        print(f"Search Error: {e}")
        return jsonify([])
    finally:
        if connection:
            connection.close()


# ==========================================
# ADMIN PANEL ROUTES
# ==========================================

@app.route('/admin')
@login_required
def admin_dashboard():
    total_posts = 0
    total_comments = 0
    total_subscribers = 0
    recent_posts = []
    connection = None

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 1. Total post count
            cursor.execute("SELECT COUNT(*) AS total FROM posts")
            res = cursor.fetchone()
            total_posts = res['total'] if res else 0

            # 2. Total comments count
            cursor.execute("SELECT COUNT(*) AS total FROM comments")
            res = cursor.fetchone()
            total_comments = res['total'] if res else 0

            # 3. Total subscribers count
            cursor.execute("SELECT COUNT(*) AS total FROM subscribers")
            res = cursor.fetchone()
            total_subscribers = res['total'] if res else 0

            # 4. Fetch 5 most recent articles
            cursor.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 5")
            recent_posts = cursor.fetchall()

    except Exception as e:
        print(f"Error loading admin dashboard: {e}")
    finally:
        if connection:
            connection.close()

    return render_template(
        'admin/dashboard.html', 
        total_posts=total_posts, 
        total_comments=total_comments, 
        total_subscribers=total_subscribers, 
        recent_posts=recent_posts
    )


@app.route('/admin/add-post', methods=['GET', 'POST'])
@login_required
def add_post():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        content = request.form.get('content', '').strip()
        image = request.files.get('image')

        if not title or not category or not content:
            flash("Please fill in all required fields.", "danger")
        elif not image or image.filename == '':
            flash("Please upload a cover image for the article.", "danger")
        elif not allowed_file(image.filename):
            flash("Invalid file type. Supported formats: PNG, JPG, JPEG, WEBP.", "danger")
        else:
            filename = secure_filename(image.filename)
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

            connection = None
            try:
                connection = get_db_connection()
                with connection.cursor() as cursor:
                    sql = "INSERT INTO posts (title, category, content, image) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql, (title, category, content, filename))
                connection.commit()
                flash("Your post has been published successfully!", "success")
                return redirect(url_for('manage_posts'))
            except Exception as e:
                print(f"Error adding post: {e}")
                flash("An error occurred while saving the post to the database.", "danger")
            finally:
                if connection:
                    connection.close()

    return render_template('admin/add_post.html')


@app.route('/admin/manage-posts')
@login_required
def manage_posts():
    posts = []
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Fetch all posts sorted by newest first
            cursor.execute("SELECT * FROM posts ORDER BY id DESC")
            posts = cursor.fetchall()
    except Exception as e:
        print(f"Error fetching posts for admin: {e}")
        posts = []
    finally:
        if connection:
            connection.close()

    return render_template('admin/manage_posts.html', posts=posts)


@app.route('/admin/delete-post/<int:id>', methods=['POST'])
@login_required
def delete_post(id):
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Retrieve image filename before deletion
            cursor.execute("SELECT image FROM posts WHERE id = %s", (id,))
            post = cursor.fetchone()

            # Delete related comments first
            cursor.execute("DELETE FROM comments WHERE post_id = %s", (id,))

            # Delete post from database
            cursor.execute("DELETE FROM posts WHERE id = %s", (id,))
            connection.commit()

            # Delete image file from upload folder if not a default template asset
            if post and post.get('image'):
                img_name = post['image'].replace('posts/', '')
                protected_defaults = {'blog1.jpg', 'blog2.jpg', 'blog3.jpg', 'author.png'}
                if img_name not in protected_defaults:
                    img_path = os.path.join(app.config['UPLOAD_FOLDER'], img_name)
                    if os.path.exists(img_path):
                        try:
                            os.remove(img_path)
                        except Exception as file_err:
                            print(f"Could not remove image file {img_path}: {file_err}")

            flash("Post and associated comments deleted successfully!", "success")
    except Exception as e:
        print(f"Error deleting post: {e}")
        flash("Failed to delete post. Please try again.", "danger")
    finally:
        if connection:
            connection.close()

    return redirect(url_for('manage_posts'))


@app.route('/admin/edit-post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = None
    connection = None

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            if request.method == 'POST':
                title = request.form.get('title', '').strip()
                category = request.form.get('category', '').strip()
                content = request.form.get('content', '').strip()
                image = request.files.get('image')

                if not title or not category or not content:
                    flash("Please fill in all required fields.", "danger")
                else:
                    # Get existing image filename
                    cursor.execute("SELECT image FROM posts WHERE id = %s", (id,))
                    current_post = cursor.fetchone()
                    old_image = current_post['image'] if current_post else None
                    new_filename = old_image
                    upload_error = False

                    # Check if a new replacement image was uploaded
                    if image and image.filename != '':
                        if allowed_file(image.filename):
                            new_filename = secure_filename(image.filename)
                            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

                            image_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                            image.save(image_path)

                            # Remove old image file if changed and not a protected default asset
                            protected_defaults = {'blog1.jpg', 'blog2.jpg', 'blog3.jpg', 'author.png'}
                            if old_image and old_image != new_filename and old_image.replace('posts/', '') not in protected_defaults:
                                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], old_image.replace('posts/', ''))
                                if os.path.exists(old_image_path):
                                    try:
                                        os.remove(old_image_path)
                                    except Exception as file_err:
                                        print(f"Could not remove old image: {file_err}")
                        else:
                            upload_error = True
                            flash("Invalid file type. Supported formats: PNG, JPG, JPEG, WEBP.", "danger")

                    if not upload_error:
                        sql_update = "UPDATE posts SET title = %s, category = %s, content = %s, image = %s WHERE id = %s"
                        cursor.execute(sql_update, (title, category, content, new_filename, id))
                        connection.commit()
                        flash("Post updated successfully!", "success")
                        return redirect(url_for('edit_post', id=id))

            # Fetch current post details to populate the form
            cursor.execute("SELECT * FROM posts WHERE id = %s", (id,))
            post = cursor.fetchone()

    except Exception as e:
        print(f"Error editing post: {e}")
        flash("An error occurred while updating the post.", "danger")
    finally:
        if connection:
            connection.close()

    return render_template('admin/edit_post.html', post=post)


@app.route('/admin/comments')
@login_required
def manage_comments():
    post_id = request.args.get('post_id', type=int)
    comments = []
    posts_list = []
    selected_post_title = None
    connection = None

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Fetch all posts to populate the article filter dropdown
            cursor.execute("SELECT id, title FROM posts ORDER BY id DESC")
            posts_list = cursor.fetchall()

            # If filtered by specific post, fetch its title and matching comments
            if post_id:
                cursor.execute("SELECT title FROM posts WHERE id = %s", (post_id,))
                selected_post = cursor.fetchone()
                if selected_post:
                    selected_post_title = selected_post['title']

                sql = """
                    SELECT c.*, p.title AS post_title 
                    FROM comments c 
                    LEFT JOIN posts p ON c.post_id = p.id 
                    WHERE c.post_id = %s
                    ORDER BY c.id DESC
                """
                cursor.execute(sql, (post_id,))
            else:
                sql = """
                    SELECT c.*, p.title AS post_title 
                    FROM comments c 
                    LEFT JOIN posts p ON c.post_id = p.id 
                    ORDER BY c.id DESC
                """
                cursor.execute(sql)

            comments = cursor.fetchall()
    except Exception as e:
        print(f"Error loading comments for admin: {e}")
        comments = []
    finally:
        if connection:
            connection.close()

    return render_template(
        'admin/comments.html',
        comments=comments,
        posts_list=posts_list,
        selected_post_id=post_id,
        selected_post_title=selected_post_title
    )


@app.route('/admin/delete-comment/<int:id>', methods=['POST'])
@login_required
def delete_comment(id):
    post_id = request.args.get('post_id', type=int)
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM comments WHERE id = %s", (id,))
            connection.commit()
        flash("Comment deleted successfully!", "success")
    except Exception as e:
        print(f"Error deleting comment: {e}")
        flash("Failed to delete comment. Please try again.", "danger")
    finally:
        if connection:
            connection.close()

    if post_id:
        return redirect(url_for('manage_comments', post_id=post_id))
    return redirect(url_for('manage_comments'))


@app.route('/admin/subscribers')
@login_required
def manage_subscribers():
    subscribers = []
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Fetch all newsletter subscribers ordered by newest first
            cursor.execute("SELECT * FROM subscribers ORDER BY id DESC")
            subscribers = cursor.fetchall()
    except Exception as e:
        print(f"Error fetching subscribers: {e}")
        subscribers = []
    finally:
        if connection:
            connection.close()

    return render_template('admin/subscribers.html', subscribers=subscribers)


@app.route('/admin/delete-subscriber/<int:id>', methods=['POST'])
@login_required
def delete_subscriber(id):
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM subscribers WHERE id = %s", (id,))
            connection.commit()
        flash("Subscriber removed successfully!", "success")
    except Exception as e:
        print(f"Error deleting subscriber: {e}")
        flash("Failed to remove subscriber. Please try again.", "danger")
    finally:
        if connection:
            connection.close()

    return redirect(url_for('manage_subscribers'))


@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect directly to dashboard
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))

    error_msg = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            error_msg = "Please enter both username and password."
        else:
            connection = None
            try:
                connection = get_db_connection()
                with connection.cursor() as cursor:
                    # Verify admin credentials against database
                    cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (username, password))
                    admin = cursor.fetchone()

                    if admin:
                        session['admin_logged_in'] = True
                        session['admin_username'] = admin.get('username', 'Admin')
                        flash(f"Welcome back, {session['admin_username']}!", "success")
                        return redirect(url_for('admin_dashboard'))
                    else:
                        error_msg = "Invalid username or password!"
            except Exception as e:
                print(f"Login Error: {e}")
                error_msg = "Database connection error. Please verify database connection."
            finally:
                if connection:
                    connection.close()

    return render_template('admin/login.html', error_msg=error_msg)


@app.route('/admin/logout')
def logout():
    # Clear admin session on logout
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
