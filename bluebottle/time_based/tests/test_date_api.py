from io import BytesIO
import icalendar
from datetime import date, timedelta

from django.urls import reverse
from openpyxl import load_workbook
from rest_framework import status

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import APITestCase
from bluebottle.time_based.serializers import (
    DateActivitySerializer,
    DateParticipantSerializer,
    DateParticipantTransitionSerializer,
    DateRegistrationSerializer,
    DateRegistrationTransitionSerializer,
    DateTransitionSerializer,
    DateActivitySlotSerializer,
)
from bluebottle.time_based.tests.base import (
    TimeBasedActivityAPIExportTestCase,
    TimeBasedActivityDetailAPITestCase,
    TimeBasedActivityListAPITestCase,
    TimeBasedActivityTransitionListAPITestCase,
    TimeBasedParticipantDetailAPITestCase,
    TimeBasedParticipantRelatedListAPITestCase,
    TimeBasedParticipantTransitionListAPITestCase,
    TimeBasedRegistrationDetailAPITestCase,
    TimeBasedRegistrationListAPITestCase,
    TimeBasedRegistrationRelatedAPIListTestCase,
    TimeBasedRegistrationTransitionListAPITestCase,
)
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateParticipantFactory,
    DateRegistrationFactory,
    DateActivitySlotFactory,
)


class DateActivityListAPITestCase(TimeBasedActivityListAPITestCase, APITestCase):
    url_name = 'date-list'
    serializer = DateActivitySerializer
    factory = DateActivityFactory

    fields = ['initiative', 'title', 'description', 'review']
    attributes = ['title', 'description', 'review']

    defaults = {
        'title': 'Test title',
        'description': 'Test description',
        'review': False,
    }

    def setUp(self):
        super().setUp()

    def test_create_complete(self, user=None, data=None):
        user = self.defaults['initiative'].owner
        self.perform_create(user=user)
        self.assertStatus(status.HTTP_201_CREATED)

        for relationship in self.relationships:
            self.assertRelationship(relationship)

        for included in self.included:
            self.assertIncluded(included)

        for attribute in self.attributes:
            self.assertAttribute(attribute)

        self.assertPermission('PUT', True)
        self.assertPermission('GET', True)
        self.assertPermission('PATCH', True)

        self.assertTransition('delete')

        # A full activity was created. Now add a slot
        slot_url = reverse('date-slot-list')
        response = self.client.post(
            slot_url,
            {
                'data': {
                    'type': 'activities/time-based/date-slots',
                    'attributes': {
                        'start': '2026-01-01 10:00:00',
                        'duration': '01:00',
                        'is-online': True
                    },
                    'relationships': {
                        'activity': {
                            'data': {
                                'id': self.response.json()['data']['id'],
                                'type': 'activities/time-based/dates'
                            }
                        }
                    }
                }
            },
            HTTP_AUTHORIZATION="JWT {0}".format(user.get_jwt_token())
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        activity = [
            resource for resource in response.json()['included']
            if resource['type'] == 'activities/time-based/dates'
        ][0]

        # Now the activity is really complete and we should be able to publish it
        self.assertTrue(
            'publish' in [transition['name'] for transition in activity['meta']['transitions']]
        )


class DateActivityDetailAPITestCase(TimeBasedActivityDetailAPITestCase, APITestCase):
    url_name = 'date-detail'
    serializer = DateActivitySerializer
    factory = DateActivityFactory

    fields = ['initiative', 'title', 'description', 'review']
    attributes = ['title', 'description', 'review']

    defaults = {
        'title': 'Test title',
        'description': 'Test description',
        'review': False,
    }

    def test_put_start_after_end(self):
        pass


class DateActivityTransitionListAPITestCase(TimeBasedActivityTransitionListAPITestCase, APITestCase):
    url_name = 'date-transition-list'
    serializer = DateTransitionSerializer
    activity_factory = DateActivityFactory
    fields = ['resource', 'transition']
    defaults = {
        'title': 'Test title',
        'description': 'Test description',
        'review': False,
    }


class DateRegistrationListAPITestCase(TimeBasedRegistrationListAPITestCase, APITestCase):
    url_name = 'date-registration-list'
    serializer = DateRegistrationSerializer
    factory = DateRegistrationFactory
    activity_factory = DateActivityFactory

    activity_defaults = {}


class DateRegistrationRelatedListAPITestCase(TimeBasedRegistrationRelatedAPIListTestCase, APITestCase):
    url_name = 'related-date-registrations'
    serializer = DateRegistrationSerializer
    factory = DateRegistrationFactory
    activity_factory = DateActivityFactory

    activity_defaults = {}


class DateRegistrationDetailAPITestCase(TimeBasedRegistrationDetailAPITestCase, APITestCase):
    url_name = 'date-registration-detail'
    serializer = DateRegistrationSerializer
    factory = DateRegistrationFactory
    activity_factory = DateActivityFactory

    activity_defaults = {}


class DateRegistrationTransitionListAPITestCase(TimeBasedRegistrationTransitionListAPITestCase, APITestCase):
    url_name = 'date-registration-transitions'
    serializer = DateRegistrationTransitionSerializer

    factory = DateRegistrationFactory
    activity_factory = DateActivityFactory
    activity_defaults = {}


class DateParticipantRelatedListAPITestCase(TimeBasedParticipantRelatedListAPITestCase, APITestCase):
    url_name = 'date-related-participants'
    serializer = DateParticipantSerializer
    factory = DateParticipantFactory

    activity_factory = DateActivityFactory

    activity_defaults = {}


class DateParticipantDetailAPITestCase(TimeBasedParticipantDetailAPITestCase, APITestCase):
    url_name = 'date-participant-detail'
    serializer = DateParticipantSerializer
    factory = DateParticipantFactory
    activity_factory = DateActivityFactory

    activity_defaults = {}


class DateParticipantTransitionListAPITestCase(TimeBasedParticipantTransitionListAPITestCase, APITestCase):
    url_name = 'date-participant-transitions'
    serializer = DateParticipantTransitionSerializer

    factory = DateParticipantFactory
    activity_factory = DateActivityFactory

    activity_defaults = {}

    transition = 'remove'
    target_status = 'removed'


class DateSlotDetailAPITestCase(APITestCase):
    url_name = 'date-slot-detail'
    serializer = DateActivitySlotSerializer
    factory = DateActivitySlotFactory

    fields = []
    attributes = []

    defaults = {}

    def setUp(self):
        super().setUp()
        self.manager = BlueBottleUserFactory.create()
        self.admin = BlueBottleUserFactory.create(is_staff=True)
        self.user = BlueBottleUserFactory.create()
        self.participant = BlueBottleUserFactory.create()
        self.activity = DateActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            review=False,
            owner=self.manager,
        )
        registration = DateRegistrationFactory.create(
            activity=self.activity,
            user=self.participant,
        )
        participant = DateParticipantFactory.create(
            registration=registration,
            activity=self.activity,
            slot=DateActivitySlotFactory.create(activity=self.activity)
        )
        self.model = participant.slot
        self.url = reverse(self.url_name, args=(self.model.pk,))

    def test_set_date_activity_manager(self):
        start = (date.today() + timedelta(days=10)).strftime('%Y-%m-%d %H:00:00')
        self.perform_update({'start': start, 'duration': '4:0:0'}, user=self.manager)
        self.assertStatus(status.HTTP_200_OK)

    def test_set_date_admin(self):
        start = (date.today() + timedelta(days=10)).strftime('%Y-%m-%d %H:00:00')
        self.perform_update({'start': start, 'duration': '4:0:0'}, user=self.admin)
        self.assertStatus(status.HTTP_200_OK)

    def test_set_date_participant(self):
        start = (date.today() + timedelta(days=10)).strftime('%Y-%m-%d %H:00:00')
        self.perform_update({'start': start, 'duration': '4:0:0'}, user=self.participant)
        self.assertStatus(status.HTTP_403_FORBIDDEN)

    def test_set_date_user(self):
        start = (date.today() + timedelta(days=10)).strftime('%Y-%m-%d %H:00:00')
        self.perform_update({'start': start, 'duration': '4:0:0'}, user=self.user)
        self.assertStatus(status.HTTP_403_FORBIDDEN)

    def test_ical_download(self):
        self.perform_get(user=self.admin)

        ical_response = self.client.get(
            self.response.json()["data"]["attributes"]["links"]["ical"],
        )

        calendar = icalendar.Calendar.from_ical(ical_response.content)

        for ical_event in calendar.walk("vevent"):
            self.assertAlmostEqual(
                ical_event["dtstart"].dt, self.model.start, delta=timedelta(seconds=10)
            )
            self.assertAlmostEqual(
                ical_event["dtend"].dt,
                self.model.start + self.model.duration,
                delta=timedelta(seconds=10),
            )

            self.assertEqual(str(ical_event["summary"]), self.activity.title)
            self.assertEqual(ical_event["url"], self.activity.get_absolute_url())
            self.assertEqual(
                ical_event["organizer"], "MAILTO:{}".format(self.activity.owner.email)
            )


class DateActivityExportTestCase(TimeBasedActivityAPIExportTestCase, APITestCase):
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory
    url_name = 'date-detail'

    activity_defaults = {}

    def test_get(self):
        self.perform_get(user=self.activity.owner)

        self.assertStatus(status.HTTP_200_OK)

        workbook = load_workbook(filename=BytesIO(self.response.content))
        self.assertEqual(len(workbook.worksheets), 5)

        sheet = workbook.get_active_sheet()

        self.assertEqual(
            tuple(sheet.values)[0],
            ('Email', 'Name', 'Registration Date', 'Status', 'Registration answer', )
        )
