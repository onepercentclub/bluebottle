from datetime import date, timedelta
from bluebottle.initiatives.tests.factories import InitiativeFactory

from bluebottle.time_based.serializers import (
    DeadlineActivitySerializer,
    DeadlineParticipantSerializer,
    DeadlineParticipantTransitionSerializer,
    DeadlineRegistrationSerializer,
    DeadlineRegistrationTransitionSerializer,
    DeadlineTransitionSerializer,
)
from bluebottle.time_based.tests.factories import (
    DeadlineActivityFactory,
    DeadlineParticipantFactory,
    DeadlineRegistrationFactory,
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

from bluebottle.test.utils import APITestCase


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
    expected_status = 'new'


class DeadlineActivityExportTestCase(TimeBasedActivityAPIExportTestCase, APITestCase):
    factory = DeadlineActivityFactory
    participant_factory = DeadlineParticipantFactory
    url_name = 'deadline-detail'

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }
