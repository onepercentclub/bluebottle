import json
from datetime import timedelta

import icalendar
from django.urls import reverse
from pytz import UTC
from rest_framework import status

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient
from bluebottle.time_based.models import Skill
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateParticipantFactory,
    SkillFactory,
)
from bluebottle.utils.utils import get_current_language


class DateTimeContributionAPIViewTestCase(BluebottleTestCase):
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory

    def setUp(self):
        super().setUp()
        self.client = JSONAPITestClient()
        self.activity = self.factory.create()
        self.participant = self.participant_factory.create(
            activity=self.activity,
            slot=self.activity.slots.first()
        )
        self.contribution = self.participant.contributions.get()

        self.url = reverse(
            'time-contribution-detail',
            args=(self.contribution.pk,)
        )
        self.data = {
            'data': {
                'type': 'contributions/time-contributions',
                'id': self.contribution.pk,
                'attributes': {
                    'value': '5:00:00'
                }
            }
        }

    def test_get_owner(self):
        response = self.client.get(self.url, user=self.activity.owner)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.json()['data']['meta']['permissions']['PUT']
        )

    def test_get_contributor(self):
        response = self.client.get(self.url, user=self.participant.user)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_other(self):
        response = self.client.get(self.url, user=BlueBottleUserFactory.create())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_anonymous(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_owner(self):
        response = self.client.put(self.url, json.dumps(self.data), user=self.activity.owner)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.contribution.refresh_from_db()

        self.assertEqual(self.contribution.value, timedelta(hours=5))

    def test_put_contributor(self):
        response = self.client.put(self.url, json.dumps(self.data), user=self.participant.user)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_other(self):
        response = self.client.put(self.url, json.dumps(self.data), user=BlueBottleUserFactory.create())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_anonymous(self):
        response = self.client.put(self.url, json.dumps(self.data))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SlotIcalTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.user = BlueBottleUserFactory.create()
        self.client = JSONAPITestClient()
        self.initiative = InitiativeFactory.create(status='approved')
        self.activity = DateActivityFactory.create(
            title='Pollute Katwijk Beach',
            owner=self.user,
            initiative=self.initiative
        )
        self.slot = self.activity.slots.first()
        self.slot.is_online = True
        self.slot.online_meeting_url = 'http://example.com'
        self.slot.location = None
        self.slot.save()

        self.slot_url = reverse('date-slot-detail', args=(self.slot.pk,))
        self.activity.states.publish(save=True)
        self.client = JSONAPITestClient()
        response = self.client.get(self.slot_url, user=self.user)
        self.signed_url = response.json()['data']['attributes']['links']['ical']
        self.unsigned_url = reverse('slot-ical', args=(self.activity.pk,))

    def test_get(self):
        response = self.client.get(self.signed_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get('content-type'), 'text/calendar')
        self.assertEqual(
            response.get('content-disposition'),
            'attachment; filename="{}.ics"'.format(self.activity.slug)
        )

        calendar = icalendar.Calendar.from_ical(response.content)

        for ical_event in calendar.walk('vevent'):
            self.assertAlmostEqual(
                ical_event['dtstart'].dt,
                self.slot.start,
                delta=timedelta(seconds=10)
            )
            self.assertAlmostEqual(
                ical_event['dtend'].dt,
                self.slot.start + self.slot.duration,
                delta=timedelta(seconds=10)
            )

            self.assertEqual(ical_event['dtstart'].dt.tzinfo, UTC)
            self.assertEqual(ical_event['dtend'].dt.tzinfo, UTC)

            self.assertEqual(str(ical_event['summary']), self.activity.title)

            self.assertEqual(ical_event['url'], self.slot.get_absolute_url())
            self.assertEqual(ical_event['organizer'], 'MAILTO:{}'.format(self.activity.owner.email))
            self.assertTrue('location' not in ical_event)

    def test_get_location(self):
        self.slot.location = GeolocationFactory.create()
        self.slot.save()

        response = self.client.get(self.signed_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        calendar = icalendar.Calendar.from_ical(response.content)

        for ical_event in calendar.walk('vevent'):
            self.assertEqual(ical_event['organizer'], 'MAILTO:{}'.format(self.activity.owner.email))
            self.assertEqual(
                ical_event['location'], self.slot.location.formatted_address
            )

    def test_get_location_hint(self):
        self.slot.location = GeolocationFactory.create()
        self.slot.location_hint = 'On the first floor'
        self.slot.save()

        response = self.client.get(self.signed_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        calendar = icalendar.Calendar.from_ical(response.content)

        for ical_event in calendar.walk('vevent'):
            self.assertEqual(ical_event['organizer'], 'MAILTO:{}'.format(self.activity.owner.email))
            self.assertEqual(
                ical_event['location'],
                f'{self.slot.location.formatted_address} ({self.slot.location_hint})'
            )

    def test_get_no_signature(self):
        response = self.client.get(self.unsigned_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_wrong_signature(self):
        response = self.client.get('{}?signature=ewiorjewoijical_url'.format(self.unsigned_url))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SkillApiTestCase(BluebottleTestCase):

    def setUp(self):
        super().setUp()
        MemberPlatformSettings.objects.update(closed=True)
        self.url = reverse('skill-list')
        Skill.objects.all().delete()
        SkillFactory.create_batch(10)
        self.client = JSONAPITestClient()

    def test_get_skills_authenticated(self):
        user = BlueBottleUserFactory.create()
        get_current_language()
        response = self.client.get(self.url, user=user, HTTP_ACCEPT_LANGUAGE='en')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 10)

    def test_get_skills_unauthenticated(self):
        response = self.client.get(self.url, HTTP_ACCEPT_LANGUAGE='en')
        self.assertEqual(response.status_code, 401)
