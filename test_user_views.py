"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False
app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_user_signup_page(self):

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = ""

                resp = c.get("/signup")
                html = resp.get_data(as_text=True)

                self.assertIn("Sign me up!", html)

                resp = c.post("/signup", data={"username":"testuser3","email":"test@test.com","password":"test"})
                html = resp.get_data(as_text=True)

                self.assertIn("testuser3", html)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/signup")
            self.assertEqual(resp.status_code, 302)

    def test_user_login(self):

        with self.client as c:

            # Checks login page without user in session. Tests get, successful post, failed post, and then user in session.
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = ""

                resp = c.get("/login")
                html = resp.get_data(as_text=True)

                self.assertIn("Log in", html)

                resp = c.post("/login", data={"username":"testuser", "password": "testuser"}, follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertIn("Hello, testuser!", html)

                resp = c.post("/login", data={"username":"testuser", "password": "testuse"}, follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertIn("Invalid credentials.", html)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/login")
            self.assertEqual(resp.status_code, 302)


    def test_user_logout(self):

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/logout")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("/login", html)

    def test_users_view(self):

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/users')
            html = resp.get_data(as_text=True)

            self.assertIn("@testuser", html)

    def test_this_user_view(self):

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/users/{self.testuser.id}')
            html = resp.get_data(as_text=True)

            self.assertIn("@testuser", html)

    def test_this_user_add_follow_view_follows_remove_follow(self):

        """Tests the current user following another, un-following another, and viewing the 'following' page upon both"""


        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            u2 = User.query.filter_by(email='test2@test.com').first()

            resp = c.post(f'/users/follow/{u2.id}')
            html = resp.get_data(as_text=True)

            self.testuser = User.query.filter_by(email='test@test.com').first()
            self.assertEqual(len(self.testuser.following), 1)
            self.assertIn(f"/users/{self.testuser.id}/following", html)

            resp = c.post(f'/users/stop-following/{u2.id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(len(self.testuser.followers), 0)
            self.assertIn(f"/users/{self.testuser.id}/following", html) #NEED TO ASSERT NOT IN


    def test_this_user_following_view_following_remove_following(self):

        """Tests the current user's followers, rendering the 'followers' page, and losing a follower"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

        u2 = User.query.filter_by(email='test2@test.com').first()

        c.post(f'/users/follow/{u2.id}')

        resp = c.get(f'/users/{u2.id}/followers')
        html = resp.get_data(as_text=True)

        u2 = User.query.filter_by(email='test2@test.com').first()
        self.assertEqual(len(u2.followers), 1)
        self.assertIn("@testuser", html)

        u2 = User.query.filter_by(email='test2@test.com').first()
        c.post(f'/users/stop-following/{u2.id}')

        u2 = User.query.filter_by(email='test2@test.com').first()
        resp = c.get(f'/users/{u2.id}/followers')
        html = resp.get_data(as_text=True)
        self.assertEqual(len(u2.followers), 0)
        self.assertIn("@testuser", html)

    def test_this_user_edit_profile(self):

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/users/profile')
            html = resp.get_data(as_text=True)

            self.assertIn("Edit this user!", html)

            resp = c.post(f'/users/profile', data={"username":"bettertest","email":"email@email.com"})
            html = resp.get_data(as_text=True)

            self.assertIn("bettertest", html)


    def test_this_user_delete(self):

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f'/users/delete')
            html = resp.get_data(as_text=True)

            resp = c.get(f'/users/{self.testuser.id}')
            self.assertEqual(resp.status_code, 404)

    def test_this_user_likes(self):

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/users/{self.testuser.id}/likes')
            html = resp.get_data(as_text=True)

            self.assertIn("Messages You've Liked:", html)