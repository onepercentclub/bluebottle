from bluebottle.deeds.models import DeedParticipant
from bluebottle.members.models import Member, MemberPlatformSettings
from bluebottle.scim.models import SCIMPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from django.test import TestCase

from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.activities.utils import bulk_add_participants


class BulkAddParticipantTestCase(TestCase):
    emails = ['ernst@goodup.com', 'loek@goodup.com', 'pieter@goodup.com']

    def setUp(self):
        self.activity = DeedFactory.create()

        self.member = BlueBottleUserFactory.create(email=self.emails[0])

    def assertParticipant(self, email):
        self.assertTrue(
            DeedParticipant.objects.filter(
                user__email=email, activity=self.activity
            ).exists()
        )

    def assertNotExists(self, email):
        self.assertFalse(
            Member.objects.filter(email=email).exists()
        )

    def test_bulk_add(self):
        result = bulk_add_participants(self.activity, self.emails, False)

        self.assertEqual(result, {
            'added': 1, 'existing': 0, 'failed': 2, 'created': 0
        })

        for email in self.emails[1:]:
            self.assertNotExists(email)

        self.assertParticipant(self.emails[0])

    def test_bulk_add_already_signed_up(self):
        DeedParticipantFactory.create(
            activity=self.activity, user=self.member
        )
        result = bulk_add_participants(self.activity, self.emails, False)

        self.assertEqual(result, {
            'added': 0, 'existing': 1, 'failed': 2, 'created': 0
        })

        for email in self.emails[1:]:
            self.assertNotExists(email)

        self.assertParticipant(self.emails[0])

    def test_bulk_closed(self):
        MemberPlatformSettings.objects.create(closed=True)
        result = bulk_add_participants(self.activity, self.emails, False)

        self.assertEqual(result, {
            'added': 1, 'existing': 0, 'failed': 0, 'created': 2
        })

        for email in self.emails:
            self.assertParticipant(email)

    def test_bulk_add_scim(self):
        MemberPlatformSettings.objects.create(closed=True)
        SCIMPlatformSettings.objects.create(enabled=True)

        result = bulk_add_participants(self.activity, self.emails, False)

        self.assertEqual(result, {
            'added': 1, 'existing': 0, 'failed': 2, 'created': 0
        })

        for email in self.emails[1:]:
            self.assertNotExists(email)

        self.assertParticipant(self.emails[0])
