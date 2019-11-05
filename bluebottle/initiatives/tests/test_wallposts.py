from django.core import mail
from django.test import TestCase
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.wallposts import MediaWallpostFactory, ReactionFactory
from bluebottle.follow.tests.factories import InitiativeFollowFactory


class InitiativeTestCase(TestCase):

    def setUp(self):
        self.initiative = InitiativeFactory.create()

        self.follower = BlueBottleUserFactory.create()
        InitiativeFollowFactory.create(
            user=self.follower, instance=self.initiative
        )
        InitiativeFollowFactory.create(
            user=BlueBottleUserFactory(campaign_notifications=False),
            instance=self.initiative
        )

        InitiativeFollowFactory.create(user=self.initiative.owner, instance=self.initiative)

    def test_wallpost(self):
        wallpost_user = BlueBottleUserFactory.create()
        MediaWallpostFactory.create(
            content_object=self.initiative, author=wallpost_user, email_followers=False
        )

        self.assertEqual(len(mail.outbox), 1)

        owner_mail = mail.outbox[0]

        self.assertEqual(
            owner_mail.subject,
            '{} commented on your initiative'.format(wallpost_user.first_name)
        )

    def test_wallpost_owner(self):
        MediaWallpostFactory.create(
            content_object=self.initiative, author=self.initiative.owner, email_followers=True
        )
        self.assertEqual(len(mail.outbox), 1)

        follow_mail = mail.outbox[0]

        self.assertEqual(
            follow_mail.subject,
            "New post on '{}'".format(self.initiative.title)
        )

    def test_reaction(self):
        reaction_user = BlueBottleUserFactory.create()
        wallpost_user = BlueBottleUserFactory.create()
        wallpost = MediaWallpostFactory.create(
            content_object=self.initiative, author=wallpost_user, email_followers=True
        )

        mail.outbox = []

        ReactionFactory.create(
            wallpost=wallpost, author=reaction_user
        )

        self.assertEqual(len(mail.outbox), 2)

        follow_mail = mail.outbox[1]

        self.assertEqual(
            follow_mail.subject,
            "New post on '{}'".format(self.initiative.title)
        )
