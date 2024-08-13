import icalendar
from datetime import date, timedelta
from io import BytesIO

from django.urls import reverse
from openpyxl import load_workbook
from rest_framework import status

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import APITestCase
from bluebottle.time_based.serializers import (
    ScheduleActivitySerializer,
    ScheduleParticipantSerializer,
    ScheduleParticipantTransitionSerializer,
    ScheduleRegistrationSerializer,
    ScheduleRegistrationTransitionSerializer,
    ScheduleTransitionSerializer, ScheduleSlotSerializer,
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
    ScheduleActivityFactory,
    ScheduleParticipantFactory,
    ScheduleRegistrationFactory,
    TeamFactory, ScheduleSlotFactory,
)


class ScheduleActivityListAPITestCase(TimeBasedActivityListAPITestCase, APITestCase):
    url_name = 'schedule-list'
    serializer = ScheduleActivitySerializer
    factory = ScheduleActivityFactory
    fields = TimeBasedActivityListAPITestCase.fields + ['capacity', 'deadline', 'duration', 'is_online']
    attributes = TimeBasedActivityListAPITestCase.attributes + [
        'capacity', 'deadline', 'duration', 'is-online'
    ]

    def setUp(self):
        super().setUp()
        self.defaults = {
            'review': False,
            'initiative': InitiativeFactory.create(status='approved', owner=self.user),
            'is_online': True,
            'duration': '02:00',
            'start': date.today() + timedelta(days=10),
            'deadline': date.today() + timedelta(days=20),
        }


class ScheduleActivityDetailAPITestCase(TimeBasedActivityDetailAPITestCase, APITestCase):
    url_name = 'schedule-detail'
    serializer = ScheduleActivitySerializer
    factory = ScheduleActivityFactory

    fields = TimeBasedActivityDetailAPITestCase.fields + ['capacity', 'deadline', 'duration', 'is_online']
    attributes = TimeBasedActivityDetailAPITestCase.attributes + [
        'capacity', 'deadline', 'duration', 'is-online'
    ]

    defaults = dict(
        TimeBasedActivityDetailAPITestCase.defaults,
        **{
            'start': date.today() + timedelta(days=10),
            'deadline': date.today() + timedelta(days=20),
        }
    )


class ScheduleActivityTransitionListAPITestCase(TimeBasedActivityTransitionListAPITestCase, APITestCase):
    url_name = 'schedule-transition-list'
    serializer = ScheduleTransitionSerializer
    activity_factory = ScheduleActivityFactory
    fields = ['resource', 'transition']

    defaults = dict(
        TimeBasedActivityDetailAPITestCase.defaults,
        **{
            'start': date.today() + timedelta(days=10),
            'deadline': date.today() + timedelta(days=20),
        }
    )


class ScheduleRegistrationListAPITestCase(TimeBasedRegistrationListAPITestCase, APITestCase):
    url_name = 'schedule-registration-list'
    serializer = ScheduleRegistrationSerializer
    factory = ScheduleRegistrationFactory
    activity_factory = ScheduleActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class ScheduleRegistrationRelatedListAPITestCase(TimeBasedRegistrationRelatedAPIListTestCase, APITestCase):
    url_name = 'related-schedule-registrations'
    serializer = ScheduleRegistrationSerializer
    factory = ScheduleRegistrationFactory
    activity_factory = ScheduleActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class ScheduleRegistrationDetailAPITestCase(TimeBasedRegistrationDetailAPITestCase, APITestCase):
    url_name = 'schedule-registration-detail'
    serializer = ScheduleRegistrationSerializer
    factory = ScheduleRegistrationFactory
    activity_factory = ScheduleActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class ScheduleRegistrationTransitionListAPITestCase(TimeBasedRegistrationTransitionListAPITestCase, APITestCase):
    url_name = 'schedule-registration-transitions'
    serializer = ScheduleRegistrationTransitionSerializer

    factory = ScheduleRegistrationFactory
    activity_factory = ScheduleActivityFactory


class ScheduleParticipantRelatedListAPITestCase(TimeBasedParticipantRelatedListAPITestCase, APITestCase):
    url_name = 'schedule-participants'
    serializer = ScheduleParticipantSerializer
    factory = ScheduleParticipantFactory

    activity_factory = ScheduleActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class ScheduleParticipantDetailAPITestCase(TimeBasedParticipantDetailAPITestCase, APITestCase):
    url_name = 'schedule-participant-detail'
    serializer = ScheduleParticipantSerializer
    factory = ScheduleParticipantFactory
    activity_factory = ScheduleActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class ScheduleParticipantTransitionListAPITestCase(TimeBasedParticipantTransitionListAPITestCase, APITestCase):
    url_name = 'schedule-participant-transitions'
    serializer = ScheduleParticipantTransitionSerializer

    factory = ScheduleParticipantFactory
    activity_factory = ScheduleActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }

    transition = 'remove'
    target_status = 'removed'


class ScheduleSlotDetailAPITestCase(APITestCase):
    url_name = 'schedule-slot-detail'
    serializer = ScheduleSlotSerializer
    factory = ScheduleSlotFactory

    fields = []
    attributes = [
        'start', 'duration'
    ]

    defaults = {}

    def setUp(self):
        super().setUp()
        self.manager = BlueBottleUserFactory.create()
        self.admin = BlueBottleUserFactory.create(is_staff=True)
        self.user = BlueBottleUserFactory.create()
        self.participant = BlueBottleUserFactory.create()
        self.activity = ScheduleActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            review=False,
            owner=self.manager,
        )
        registration = ScheduleRegistrationFactory.create(
            activity=self.activity,
            user=self.participant,
        )
        participant = registration.participants.first()
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
        start = (date.today() + timedelta(days=10)).strftime("%Y-%m-%d %H:00:00")
        self.perform_update(
            {"start": start, "duration": "4:0:0", "is_online": True}, user=self.admin
        )

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


class ScheduleActivityExportTestCase(TimeBasedActivityAPIExportTestCase, APITestCase):
    factory = ScheduleActivityFactory
    participant_factory = ScheduleParticipantFactory
    url_name = 'schedule-detail'

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class TeamScheduleActivityExportTestCase(
    TimeBasedActivityAPIExportTestCase, APITestCase
):
    factory = ScheduleActivityFactory
    participant_factory = TeamFactory
    url_name = "schedule-detail"

    activity_defaults = {
        "start": date.today() + timedelta(days=10),
        "deadline": date.today() + timedelta(days=20),
        "team_activity": "teams",
    }

    def test_get(self):
        self.perform_get(user=self.activity.owner)

        self.assertStatus(status.HTTP_200_OK)

        workbook = load_workbook(filename=BytesIO(self.response.content))
        self.assertEqual(len(workbook.worksheets), self.activity.teams.count() + 1)

        sheet = workbook.get_active_sheet()

        self.assertEqual(len(tuple(sheet.values)), self.activity.teams.count() + 1)

        self.assertEqual(
            tuple(sheet.values)[0],
            (
                "Captain email",
                "Captain name",
                "Registration Date",
                "Status",
                "Registration answer",
            ),
        )

        for sheet in workbook.worksheets[1:]:
            self.assertEqual(
                tuple(sheet.values)[0],
                (
                    "Email",
                    "Name",
                    "Registration Date",
                    "Status",
                    "Is captain",
                ),
            )
