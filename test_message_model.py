"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


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


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_message_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        # Given an existing user...
        db.session.add(u)
        db.session.commit()

        # Does a message work?
        message = Message(text="whatever", user_id=u.id)
        db.session.add(message)
        db.session.commit()

        # Tests that the message has been added to DB and now has an id
        self.assertEqual(message.id, 1)
        self.assertEqual(message.user, u)



    def test_message_creation_failure(self):
        """Do various method failures produce proper failures?"""

        # Adds a user and improper message
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        message = Message(text="whatever", user_id="")
        message2 = Message(text="", user_id=u.id)



        db.session.add(message)
        db.session.add(message2)

        # self.asserError(whenever they commit?)



   