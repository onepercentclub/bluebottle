from datetime import date, timedelta
from bluebottle.initiatives.tests.factories import InitiativeFactory

from bluebottle.time_based.serializers import (
    PeriodicActivitySerializer,
    PeriodicParticipantSerializer,
    PeriodicParticipantTransitionSerializer,
    PeriodicRegistrationSerializer,
    PeriodicRegistrationTransitionSerializer,
    PeriodicTransitionSerializer,
)
from bluebottle.time_based.tests.factories import (
    PeriodicActivityFactory,
    PeriodicParticipantFactory,
    PeriodicRegistrationFactory,
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


class PeriodicActivityListAPITestCase(TimeBasedActivityListAPITestCase, APITestCase):
    url_name = 'periodic-list'
    serializer = PeriodicActivitySerializer
    factory = PeriodicActivityFactory
    fields = TimeBasedActivityListAPITestCase.fields + ['capacity', 'period', 'duration', 'deadline', 'is_online']
    attributes = TimeBasedActivityListAPITestCase.attributes + [
        'capacity', 'period', 'duration', 'is-online', 'deadline'
    ]

    def setUp(self):
        super().setUp()
        self.defaults = {
            'review': False,
            'initiative': InitiativeFactory.create(status='approved', owner=self.user),
            'is_online': True,
            'duration': '02:00',
            'period': 'weeks',
            'start': date.today() + timedelta(days=10),
            'deadline': date.today() + timedelta(days=20),
        }


class PeriodicActivityDetailAPITestCase(TimeBasedActivityDetailAPITestCase, APITestCase):
    url_name = 'periodic-detail'
    serializer = PeriodicActivitySerializer
    factory = PeriodicActivityFactory

    fields = TimeBasedActivityDetailAPITestCase.fields + ['capacity', 'periodic', 'duration', 'is_online']
    attributes = TimeBasedActivityDetailAPITestCase.attributes + [
        'capacity', 'duration', 'period', 'duration', 'is-online'
    ]

    defaults = dict(
        TimeBasedActivityDetailAPITestCase.defaults,
        **{
            'start': date.today() + timedelta(days=10),
            'deadline': date.today() + timedelta(days=20),
        }
    )


class PeriodicActivityTransitionListAPITestCase(TimeBasedActivityTransitionListAPITestCase, APITestCase):
    url_name = 'periodic-transition-list'
    serializer = PeriodicTransitionSerializer
    activity_factory = PeriodicActivityFactory
    fields = ['resource', 'transition']

    defaults = dict(
        TimeBasedActivityDetailAPITestCase.defaults,
        **{
            'start': date.today() + timedelta(days=10),
            'deadline': date.today() + timedelta(days=20),
        }
    )


class PeriodicRegistrationListAPITestCase(TimeBasedRegistrationListAPITestCase, APITestCase):
    url_name = 'periodic-registration-list'
    serializer = PeriodicRegistrationSerializer
    factory = PeriodicRegistrationFactory
    activity_factory = PeriodicActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class PeriodicRegistrationRelatedListAPITestCase(TimeBasedRegistrationRelatedAPIListTestCase, APITestCase):
    url_name = 'related-periodic-registrations'
    serializer = PeriodicRegistrationSerializer
    factory = PeriodicRegistrationFactory
    activity_factory = PeriodicActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class PeriodicRegistrationDetailAPITestCase(TimeBasedRegistrationDetailAPITestCase, APITestCase):
    url_name = 'periodic-registration-detail'
    serializer = PeriodicRegistrationSerializer
    factory = PeriodicRegistrationFactory
    activity_factory = PeriodicActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class PeriodicRegistrationTransitionListAPITestCase(TimeBasedRegistrationTransitionListAPITestCase, APITestCase):
    url_name = 'periodic-registration-transitions'
    serializer = PeriodicRegistrationTransitionSerializer

    factory = PeriodicRegistrationFactory
    activity_factory = PeriodicActivityFactory


class PeriodicParticipantRelatedListAPITestCase(TimeBasedParticipantRelatedListAPITestCase, APITestCase):
    url_name = 'periodic-participants'
    serializer = PeriodicParticipantSerializer
    factory = PeriodicParticipantFactory

    activity_factory = PeriodicActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class PeriodicParticipantDetailAPITestCase(TimeBasedParticipantDetailAPITestCase, APITestCase):
    url_name = 'periodic-participant-detail'
    serializer = PeriodicParticipantSerializer
    factory = PeriodicParticipantFactory
    activity_factory = PeriodicActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class PeriodicParticipantTransitionListAPITestCase(TimeBasedParticipantTransitionListAPITestCase, APITestCase):
    url_name = 'periodic-participant-transitions'
    serializer = PeriodicParticipantTransitionSerializer

    factory = PeriodicParticipantFactory
    activity_factory = PeriodicActivityFactory

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }
    transition = 'remove'
    target_status = 'removed'


class PeriodicActivityExportTestCase(TimeBasedActivityAPIExportTestCase, APITestCase):
    factory = PeriodicActivityFactory
    participant_factory = PeriodicParticipantFactory
    url_name = 'periodic-detail'

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }
