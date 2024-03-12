from datetime import date, timedelta

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import APITestCase
from bluebottle.time_based.serializers import (
    ScheduleActivitySerializer,
    ScheduleParticipantSerializer,
    ScheduleParticipantTransitionSerializer,
    ScheduleRegistrationSerializer,
    ScheduleRegistrationTransitionSerializer,
    ScheduleTransitionSerializer,
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


class ScheduleActivityExportTestCase(TimeBasedActivityAPIExportTestCase, APITestCase):
    factory = ScheduleActivityFactory
    participant_factory = ScheduleParticipantFactory
    url_name = 'schedule-detail'

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }
