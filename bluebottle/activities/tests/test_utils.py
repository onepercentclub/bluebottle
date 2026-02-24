from datetime import datetime
from html import unescape

from django.test import TestCase

from bluebottle.activities.utils import bulk_add_participants
from bluebottle.deeds.models import DeedParticipant
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.members.models import Member, MemberPlatformSettings
from bluebottle.scim.models import SCIMPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from bluebottle.activities.ical import ActivityIcal

from bluebottle.collect.tests.factories import CollectActivityFactory
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.test.utils import BluebottleTestCase


from bluebottle.time_based.tests.factories import (
    DateActivityFactory, DateActivitySlotFactory, ScheduleSlotFactory
)
from bluebottle.utils.utils import to_text


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


class IcalTestMixin:
    defaults = {}

    def setUp(self):
        self.model = self.factory.create(
            **self.defaults
        )

        self.ical = ActivityIcal(self.model)
        self.ics = self.ical.to_file().decode('utf-8')

        super().setUp()

    def assert_field(self, field, value):
        for line in self.ics.replace('\r\n ', '').splitlines():
            if line.startswith(field):
                self.assertIn(
                    value, line
                )
                return

        self.fail(f'Field {field} not found')

    def test_summary(self):
        if hasattr(self.model, 'activity'):
            self.assert_field('SUMMARY', self.model.activity.title)
        else:
            self.assert_field('SUMMARY', self.model.title)

    def test_url(self):
        self.assert_field('URL', self.model.get_absolute_url())

    def test_uid(self):
        self.assert_field('UID', self.model.uid)

    def test_description(self):
        if hasattr(self.model, 'activity'):
            description = self.model.activity.description
        else:
            description = self.model.description

        escaped = unescape(
            to_text.handle(description.html)
        )[:-1]

        self.assert_field(
            'DESCRIPTION',
            f'{escaped}\, {self.model.get_absolute_url()}'
        )

    def test_orgnanizer(self):
        self.assert_field(
            'ORGANIZER',
            f'CN="{self.model.owner.full_name}":MAILTO:{self.model.owner.email}'
        )

    def test_start(self):
        if isinstance(self.model.start, datetime):
            self.assert_field(
                'DTSTART',
                f'TZID=UTC;VALUE=DATE-TIME:{self.model.start.strftime("%Y%m%dT%H%M%SZ")}'
            )
        else:
            self.assert_field(
                'DTSTART',
                f'VALUE=DATE:{self.model.start.strftime("%Y%m%d")}'
            )

    def test_end(self):
        if isinstance(self.model.start, datetime):
            self.assert_field(
                'DTEND',
                f'TZID=UTC;VALUE=DATE-TIME:{self.model.end.strftime("%Y%m%dT%H%M%SZ")}'
            )
        else:
            self.assert_field(
                'DTEND',
                f'VALUE=DATE:{self.model.end.strftime("%Y%m%d")}'
            )


class DeedIcalTestCase(IcalTestMixin, BluebottleTestCase):
    factory = DeedFactory


class CollectIcalTestCase(IcalTestMixin, BluebottleTestCase):
    factory = CollectActivityFactory

    def test_description(self):
        description = unescape(
            to_text.handle(self.model.description.html)
        )[:-1]
        self.assert_field(
            'DESCRIPTION',
            f'{description}\, Collecting {self.model.collect_type}\, {self.model.get_absolute_url()}'
        )


class ScheduleSlotIcalTestCase(IcalTestMixin, BluebottleTestCase):
    factory = ScheduleSlotFactory

    @property
    def defaults(self):
        return {
            'location': GeolocationFactory.create(),
            'location_hint': "On the third floor",
        }

    def test_location(self):
        self.assert_field(
            'LOCATION', f'{self.model.location.formatted_address} ({self.model.location_hint})'
        )


class DateActivitySlotIcalTestCase(IcalTestMixin, BluebottleTestCase):
    factory = DateActivitySlotFactory

    @property
    def defaults(self):
        return {
            'activity': DateActivityFactory.create(slots=[]),
            'location': GeolocationFactory.create(),
            'location_hint': "On the third floor",
        }

    def test_location(self):
        self.assert_field(
            'LOCATION', f'{self.model.location.formatted_address} ({self.model.location_hint})'
        )


class OnlineDateActivitySlotIcalTestCase(IcalTestMixin, BluebottleTestCase):
    factory = DateActivitySlotFactory

    @property
    def defaults(self):
        return {
            'activity': DateActivityFactory.create(slots=[]),
            'is_online': True,
            'online_meeting_url': "http://example.com",
        }

    def test_description(self):
        description = unescape(
            to_text.handle(self.model.activity.description.html)
        )[:-1]
        self.assert_field(
            'DESCRIPTION',
            f'{description}\, {self.model.get_absolute_url()} Join: {self.model.online_meeting_url}'
        )
