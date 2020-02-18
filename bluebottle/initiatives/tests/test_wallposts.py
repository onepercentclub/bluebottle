from django.core import mail
from django.test import TestCase
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.events.tests.factories import EventFactory
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.wallposts import MediaWallpostFactory, ReactionFactory
from bluebottle.follow.tests.factories import (
    EventFollowFactory, FundingFollowFactory
)


class InitiativeWallpostTestCase(TestCase):

    def setUp(self):
        self.initiative = InitiativeFactory.create()

        self.follower = BlueBottleUserFactory.create()
        EventFollowFactory.create(
            instance=EventFactory.create(
                review_status='approved',
                initiative=self.initiative
            ),
            user=self.follower
        )
        FundingFollowFactory.create(
            instance=FundingFactory.create(
                review_status='approved',
                initiative=self.initiative
            ),
            user=self.follower
        )

        EventFollowFactory.create(
            instance=EventFactory.create(
                review_status='approved',
                initiative=self.initiative
            ),
            user=BlueBottleUserFactory(campaign_notifications=False),
        )

        EventFollowFactory.create(
            instance=EventFactory.create(
                review_status='approved',
                initiative=self.initiative
            ),
            user=self.initiative.owner
        )

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

        wallpost_owner_mail = mail.outbox[0]

        self.assertEqual(
            wallpost_owner_mail.subject,
            "{} replied on your comment".format(reaction_user.first_name)
        )
        owner_mail = mail.outbox[1]

        self.assertEqual(
            owner_mail.subject,
            "{} commented on your initiative".format(reaction_user.first_name)
        )
