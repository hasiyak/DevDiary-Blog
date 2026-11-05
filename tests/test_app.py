import os
import sqlite3
import tempfile
import unittest

from app import create_app


class DevDiaryAppTests(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app(
            {
                "TESTING": True,
                "DATABASE": self.db_path,
                "SECRET_KEY": "test-secret",
                "ADMIN_USERNAME": "admin",
                "ADMIN_PASSWORD": "secret-pass",
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def login(self):
        return self.client.post(
            "/admin/login",
            data={"username": "admin", "password": "secret-pass"},
            follow_redirects=True,
        )

    def test_admin_requires_login(self):
        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login", response.location)

    def test_crud_post_flow(self):
        login_response = self.login()
        self.assertEqual(login_response.status_code, 200)
        self.assertIn(b"Admin Dashboard", login_response.data)

        create_response = self.client.post(
            "/admin/posts/new",
            data={"title": "My First Post", "slug": "", "content": "<p>Hello world</p>"},
            follow_redirects=True,
        )
        self.assertEqual(create_response.status_code, 200)
        self.assertIn(b"My First Post", create_response.data)

        with sqlite3.connect(self.db_path) as db:
            post = db.execute("SELECT id, slug FROM posts WHERE title = ?", ("My First Post",)).fetchone()
        self.assertIsNotNone(post)
        post_id = post[0]

        edit_response = self.client.post(
            f"/admin/posts/{post_id}/edit",
            data={"title": "Updated Post", "slug": post[1], "content": "<p>Updated content</p>"},
            follow_redirects=True,
        )
        self.assertEqual(edit_response.status_code, 200)
        self.assertIn(b"Updated Post", edit_response.data)

        detail_response = self.client.get(f"/post/{post[1]}")
        self.assertEqual(detail_response.status_code, 200)
        self.assertIn(b"Updated content", detail_response.data)

        delete_response = self.client.post(f"/admin/posts/{post_id}/delete", follow_redirects=True)
        self.assertEqual(delete_response.status_code, 200)
        self.assertNotIn(b"Updated Post", delete_response.data)

    def test_newsletter_subscription_endpoint(self):
        invalid = self.client.post("/subscribe", data={"email": "not-an-email"})
        self.assertEqual(invalid.status_code, 400)

        valid = self.client.post("/subscribe", data={"email": "user@example.com"})
        self.assertEqual(valid.status_code, 200)
        self.assertIn(b"Thanks for subscribing", valid.data)

        duplicate = self.client.post("/subscribe", data={"email": "user@example.com"})
        self.assertEqual(duplicate.status_code, 409)


if __name__ == "__main__":
    unittest.main()
