"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        # User can be created and added
        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

        # User repr method works properly
        self.assertEqual(repr(u), f'<User #{u.id}: testuser, test@test.com>')

        db.session.delete(u)
        db.session.commit()

    def test_user_model_following(self):
        """Do the following methods work for users?"""

        # Adds 2 users and links them via follow
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.add(u2)
        u.followers.append(u2)
        db.session.commit()

        # Checks that, once following, both users show that relationship
        self.assertEqual(u.followers[0].id, u2.id)
        self.assertEqual(u2.following[0].id, u.id)

        u.followers.remove(u2)
        db.session.commit()

        # Unfollows and verifies the relationship is broken
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(len(u2.following), 0)

        db.session.delete(u)
        db.session.delete(u2)
        db.session.commit()

    def test_user_creation_failures(self):
        """Will the creation of users fail when passed incorrect info?"""

        u = User(
            email="",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test2@email.com",
            username="",
            password="HASHED_PASSWORD"
        )

        u3 = User(
            email="test3@email.com",
            username="testuser",
            password=""
        )

        db.session.add(u)
        db.session.commit()

        # self.asserError(whenever they commit?)
        # db.session.delete(u)
        # db.session.delete(u2)
        # db.session.delete(u3)
        # db.session.commit()

    def test_user_authentication(self):
        """Does user properly authenticate?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # Checkes if the authentication process works properly and fails properly
        self.assertEqual(User.authenticate('testuser', 'HASHED_PASSWORD'), u)
        self.assertEqual(User.authenticate('testuse', 'HASHED_PASSWORD'), False)
        self.assertEqual(User.authenticate('testuser', 'HASHED_PASSWORD'), False)

        db.session.delete(u)
        db.session.commit()