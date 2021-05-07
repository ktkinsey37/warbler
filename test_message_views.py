"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


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


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        u2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.add(self.testuser)
        db.session.add(u2)
        db.session.commit()

        msg = Message(text="hello", user_id=self.testuser.id)

        db.session.add(msg)
        db.session.commit()

    def test_add_and_delete_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            test_msg = Message.query.filter_by(user_id=self.testuser.id).first()
            self.assertEqual(test_msg.text, "hello")

            resp = c.post(f"/messages/{test_msg.id}/delete")

            self.assertEqual(resp.status_code, 200)

            self.testuser = User.query.filter_by(id=self.testuser.id).first()
            self.assertEqual(test_msg in self.testuser.messages, False)

    def test_add_and_delete_msg_unauthenticated(self):
        """Will an unathenticated user fail to delete message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess.pop(CURR_USER_KEY)

            resp = c.post("/messages/new", data={"text": "Hello"})
            html = resp.get_data(as_text=True)

            # Make sure it throws an error and redirect
            self.assertEqual(resp.status_code, 302)
            self.assertIn("Access unauthorized.", html)

            msg = Message.query.filter_by(user_id=u2.id).one()
            resp = c.post(f"/messages/{msg.id}/delete", data={"text": "Hello"})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 302)
            self.assertIn("Access unauthorized.", html)

    def test_add_and_delete_msg_unauthorized(self):
        """Will an unauthorized user fail to delete message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            u2 = User.query.filter_by(username='testuser2').first()
            fake_msg = Message(text="fake", user_id=u2.id)

            resp = c.post("/messages/new", data={"text": "fake", "user_id": f"{u2.id}"})
            # THIS KIND OF ATTACK WORKS! POSTS A MESSAGE UNDER THE WRONG USER
            # Maybe it doesnt? Seems liek sql might break it

    def test_msg_view(self):

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            self.testuser = User.query.filter_by(id=self.testuser.id).first()
            msg = self.testuser.messages[0]

            resp = c.get(f"/messages/{msg.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("hello", html)

    def test_msg_like(self):

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id


            self.testuser = User.query.filter_by(id=self.testuser.id).first()
            msg = self.testuser.messages[0]

            resp = c.post(f"/users/add_like/{msg.id}")

            self.testuser = User.query.filter_by(id=self.testuser.id).first()

            self.assertEqual(len(self.testuser.likes), 1)
