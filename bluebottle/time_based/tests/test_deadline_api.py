from datetime import date, timedelta
from io import BytesIO

from django.utils.timezone import now
from openpyxl import load_workbook
from rest_framework import status

from bluebottle.activities.models import RemoteContributor
from bluebottle.activity_pub.tests.factories import DoGoodEventFactory, OrganizationFactory
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

    def test_contributor_count_uses_remote_total_for_synced_activity(self):
        self.model.origin = DoGoodEventFactory.create(contributor_count=6)
        self.model.save(update_fields=['origin'])
        DeadlineParticipantFactory.create(activity=self.model, status='accepted')

        self.perform_get(user=self.model.owner)
        self.assertStatus(status.HTTP_200_OK)
        self.assertMeta('contributor-count', 6)


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

    def test_get_remote_contributor_display_name_and_platform(self):
        platform_actor = OrganizationFactory.create(name='Partner Platform')
        remote_contributor = RemoteContributor.objects.create(
            display_name='Remote Deadline Participant',
            email='remote@example.com',
            sync_id='deadline-remote-1',
            sync_actor=platform_actor,
        )
        participant = DeadlineParticipantFactory.create(
            activity=self.activity,
            user=None,
            remote_contributor=remote_contributor,
            status='succeeded',
        )

        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)

        payload = next(
            item for item in self.response.json()['data']
            if item['id'] == str(participant.pk)
        )
        self.assertEqual(
            payload['attributes']['display-name'],
            'Remote Deadline Participant'
        )
        self.assertEqual(payload['attributes']['platform'], 'Partner Platform')


class DeadlineParticipantDetailAPITestCase(TimeBasedParticipantDetailAPITestCase, APITestCase):
    url_name = 'deadline-participant-detail'
    serializer = DeadlineParticipantSerializer
    factory = DeadlineParticipantFactory
    activity_factory = DeadlineActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }

    def test_get_remote_contributor_display_name_and_platform(self):
        platform_actor = OrganizationFactory.create(name='Partner Platform')
        remote_contributor = RemoteContributor.objects.create(
            display_name='Remote Deadline Participant',
            email='remote@example.com',
            sync_id='deadline-remote-2',
            sync_actor=platform_actor,
        )
        self.participant.user = None
        self.participant.remote_contributor = remote_contributor
        self.participant.save(update_fields=['user', 'remote_contributor'])

        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)

        attributes = self.response.json()['data']['attributes']
        self.assertEqual(
            attributes['display-name'],
            'Remote Deadline Participant'
        )
        self.assertEqual(attributes['platform'], 'Partner Platform')


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
        segment1 = SegmentFactory.create(
            segment_type=segment_type,
            slug='vis',
            name='Vis'
        )
        segment2 = SegmentFactory.create(
            segment_type=segment_type,
            slug='vlees',
            name='Vlees'
        )
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
