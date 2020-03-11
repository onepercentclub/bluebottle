from django.core import mail
from django.test import TestCase
from bluebottle.events.tests.factories import EventFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.wallposts import MediaWallpostFactory, ReactionFactory
from bluebottle.follow.tests.factories import EventFollowFactory


class ActivityWallpostTestCase(TestCase):

    def setUp(self):
        self.activity = EventFactory.create()

        self.follower = BlueBottleUserFactory.create()
        EventFollowFactory.create(
            user=self.follower, instance=self.activity
        )
        EventFollowFactory.create(
            user=BlueBottleUserFactory(campaign_notifications=False),
            instance=self.activity
        )

        EventFollowFactory.create(user=self.activity.owner, instance=self.activity)

    def test_wallpost(self):
        wallpost_user = BlueBottleUserFactory.create()
        MediaWallpostFactory.create(
            content_object=self.activity, author=wallpost_user, email_followers=False
        )

        self.assertEqual(len(mail.outbox), 1)

        owner_mail = mail.outbox[0]

        self.assertEqual(
            owner_mail.subject,
            "You have a new post on '{}'".format(self.activity.title)
        )
        self.assertTrue(
            "{} posted a comment to '{}'.".format(wallpost_user.first_name, self.activity.title)
            in owner_mail.body
        )

    def test_wallpost_owner(self):
        MediaWallpostFactory.create(
            content_object=self.activity, author=self.activity.owner, email_followers=True
        )
        self.assertEqual(len(mail.outbox), 1)

        follow_mail = mail.outbox[0]

        self.assertEqual(
            follow_mail.subject,
            "Update from '{}'".format(self.activity.title)
        )

    def test_reaction(self):
        reaction_user = BlueBottleUserFactory.create()
        wallpost_user = BlueBottleUserFactory.create()
        wallpost = MediaWallpostFactory.create(
            content_object=self.activity, author=wallpost_user, email_followers=True
        )

        mail.outbox = []

        ReactionFactory.create(
            wallpost=wallpost, author=reaction_user
        )

        self.assertEqual(len(mail.outbox), 2)

        wallpost_owner_mail = mail.outbox[0]

        self.assertEqual(
            wallpost_owner_mail.subject,
            "You have a new post on '{}'".format(self.activity.title)
        )
        owner_mail = mail.outbox[1]

        self.assertEqual(
            owner_mail.subject,
            "You have a new post on '{}'".format(self.activity.title)
        )
