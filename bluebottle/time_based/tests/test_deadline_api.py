from datetime import date, timedelta
from io import BytesIO

from django.utils.timezone import now
from openpyxl import load_workbook
from rest_framework import status

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.segments.tests.factories import SegmentTypeFactory, SegmentFactory
from bluebottle.test.factory_models.projects import ThemeFactory
from bluebottle.test.utils import APITestCase
from bluebottle.time_based.serializers import (
    DeadlineActivitySerializer,
    DeadlineParticipantSerializer,
    DeadlineParticipantTransitionSerializer,
    DeadlineRegistrationSerializer,
    DeadlineRegistrationTransitionSerializer,
    DeadlineTransitionSerializer,
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
    DeadlineActivityFactory,
    DeadlineParticipantFactory,
    DeadlineRegistrationFactory,
)


class DeadlineActivityListAPITestCase(TimeBasedActivityListAPITestCase, APITestCase):
    url_name = 'deadline-list'
    serializer = DeadlineActivitySerializer
    factory = DeadlineActivityFactory
    fields = TimeBasedActivityListAPITestCase.fields + ['capacity', 'deadline', 'duration', 'is_online']
    attributes = TimeBasedActivityListAPITestCase.attributes + [
        'capacity', 'deadline', 'duration', 'is-online'
    ]

    def setUp(self):
        super().setUp()
        self.defaults = {
            'review': False,
            'initiative': InitiativeFactory.create(status='approved', owner=self.user),
            'theme': ThemeFactory.create(),
            'is_online': True,
            'duration': '02:00',
            'start': date.today() + timedelta(days=10),
            'deadline': date.today() + timedelta(days=20),
        }


class DeadlineActivityDetailAPITestCase(TimeBasedActivityDetailAPITestCase, APITestCase):
    url_name = 'deadline-detail'
    serializer = DeadlineActivitySerializer
    factory = DeadlineActivityFactory

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

    def test_registration_count(self):
        DeadlineRegistrationFactory.create_batch(1, status="new", activity=self.model)
        DeadlineRegistrationFactory.create_batch(
            2, status="rejected", activity=self.model
        )
        DeadlineRegistrationFactory.create_batch(
            3, status="accepted", activity=self.model
        )

        self.perform_get(user=self.model.owner)

        self.assertMeta("registration-status", {"accepted": 3, "new": 1, "rejected": 2})


class DeadlineActivityTransitionListAPITestCase(TimeBasedActivityTransitionListAPITestCase, APITestCase):
    url_name = 'deadline-transition-list'
    serializer = DeadlineTransitionSerializer
    activity_factory = DeadlineActivityFactory
    fields = ['resource', 'transition']

    defaults = dict(
        TimeBasedActivityDetailAPITestCase.defaults,
        **{
            'start': date.today() + timedelta(days=10),
            'deadline': date.today() + timedelta(days=20),
        }
    )


class DeadlineRegistrationListAPITestCase(TimeBasedRegistrationListAPITestCase, APITestCase):
    url_name = 'deadline-registration-list'
    serializer = DeadlineRegistrationSerializer
    factory = DeadlineRegistrationFactory
    activity_factory = DeadlineActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class DeadlineRegistrationRelatedListAPITestCase(TimeBasedRegistrationRelatedAPIListTestCase, APITestCase):
    url_name = 'related-deadline-registrations'
    serializer = DeadlineRegistrationSerializer
    factory = DeadlineRegistrationFactory
    activity_factory = DeadlineActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class DeadlineRegistrationDetailAPITestCase(TimeBasedRegistrationDetailAPITestCase, APITestCase):
    url_name = 'deadline-registration-detail'
    serializer = DeadlineRegistrationSerializer
    factory = DeadlineRegistrationFactory
    activity_factory = DeadlineActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class DeadlineRegistrationTransitionListAPITestCase(TimeBasedRegistrationTransitionListAPITestCase, APITestCase):
    url_name = 'deadline-registration-transitions'
    serializer = DeadlineRegistrationTransitionSerializer

    factory = DeadlineRegistrationFactory
    activity_factory = DeadlineActivityFactory


class DeadlineParticipantRelatedListAPITestCase(TimeBasedParticipantRelatedListAPITestCase, APITestCase):
    url_name = 'deadline-participants'
    serializer = DeadlineParticipantSerializer
    factory = DeadlineParticipantFactory

    activity_factory = DeadlineActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class DeadlineParticipantDetailAPITestCase(TimeBasedParticipantDetailAPITestCase, APITestCase):
    url_name = 'deadline-participant-detail'
    serializer = DeadlineParticipantSerializer
    factory = DeadlineParticipantFactory
    activity_factory = DeadlineActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class DeadlineParticipantTransitionListAPITestCase(TimeBasedParticipantTransitionListAPITestCase, APITestCase):
    url_name = 'deadline-participant-transitions'
    serializer = DeadlineParticipantTransitionSerializer

    factory = DeadlineParticipantFactory
    activity_factory = DeadlineActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }

    transition = 'remove'
    target_status = 'removed'


class DeadlineActivityExportTestCase(TimeBasedActivityAPIExportTestCase, APITestCase):
    factory = DeadlineActivityFactory
    participant_factory = DeadlineParticipantFactory
    url_name = 'deadline-detail'

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }

    def test_get_with_segments(self):
        segment_type = SegmentTypeFactory.create()
        segment1 = SegmentFactory.create(segment_type=segment_type)
        segment1.name = 'Vis'
        segment1.save()
        segment2 = SegmentFactory.create(segment_type=segment_type)
        segment2.name = 'Vlees'
        segment2.save()
        self.participants[0].user.segments.add(segment1)
        reg_date = now() - timedelta(days=10)
        self.participants[1].user.segments.add(segment1)
        self.participants[1].user.segments.add(segment2)
        for p in self.participants:
            p.created = reg_date
            p.save()

        self.perform_get(user=self.activity.owner)

        self.assertStatus(status.HTTP_200_OK)

        workbook = load_workbook(filename=BytesIO(self.response.content))
        self.assertEqual(len(workbook.worksheets), 1)

        sheet = workbook.get_active_sheet()

        self.assertEqual(
            tuple(sheet.values)[0],
            ('Email', 'Name', 'Registration Date', 'Status', 'Registration answer', segment_type.name)
        )

        user = self.participants[0].user

        self.assertEqual(
            tuple(sheet.values)[1],
            (user.email, user.full_name, reg_date.strftime('%d-%m-%y %H:%M'), 'new', None, segment1.name)
        )

        user = self.participants[1].user
        self.assertEqual(
            tuple(sheet.values)[2],
            (user.email, user.full_name, reg_date.strftime('%d-%m-%y %H:%M'), 'new', None,
             f"{segment1.name}, {segment2.name}")
        )
