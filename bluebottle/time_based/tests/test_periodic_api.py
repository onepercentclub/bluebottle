from datetime import date, timedelta

from django.core import mail
from rest_framework import status

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import APITestCase
from bluebottle.time_based.serializers import (
    PeriodicActivitySerializer,
    PeriodicParticipantSerializer,
    PeriodicParticipantTransitionSerializer,
    PeriodicRegistrationSerializer,
    PeriodicRegistrationTransitionSerializer,
    PeriodicTransitionSerializer,
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
    PeriodicActivityFactory,
    PeriodicParticipantFactory,
    PeriodicRegistrationFactory,
)


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

    def test_stop_by_manager(self):
        self.perform_create(user=self.activity.owner)
        self.assertResourceStatus(self.registration, "accepted")
        mail.outbox = []
        self.defaults["transition"] = "stop"
        self.defaults["message"] = "We don't need you anymore."
        self.perform_create(user=self.activity.owner)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertResourceStatus(self.registration, "stopped")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            f'Your contribution to the activity "{self.activity.title}" has been stopped',
        )
        self.assertTrue("We don't need you anymore." in mail.outbox[0].body)

    def test_restart_by_manager(self):
        self.perform_create(user=self.activity.owner)
        self.assertResourceStatus(self.registration, "accepted")
        self.defaults["transition"] = "stop"
        self.defaults["message"] = "We don't need you anymore."
        self.perform_create(user=self.activity.owner)
        mail.outbox = []
        self.defaults["transition"] = "start"
        self.defaults["message"] = "Good to have you back!"
        self.perform_create(user=self.activity.owner)
        self.assertResourceStatus(self.registration, "accepted")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            f'Your contribution to the activity "{self.activity.title}" has been restarted',
        )
        self.assertTrue("Good to have you back!" in mail.outbox[0].body)

    def test_stop_no_mail(self):
        self.perform_create(user=self.activity.owner)
        mail.outbox = []
        self.defaults["transition"] = "stop"
        self.defaults["send_email"] = False
        self.perform_create(user=self.activity.owner)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertResourceStatus(self.registration, "stopped")
        self.assertEqual(len(mail.outbox), 0)

    def test_stop_self(self):
        self.perform_create(user=self.activity.owner)
        self.assertStatus(status.HTTP_201_CREATED)
        mail.outbox = []
        self.defaults["transition"] = "stop"
        self.perform_create(user=self.registration.user)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertResourceStatus(self.registration, "stopped")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            f'Your contribution to the activity "{self.activity.title}" has been stopped',
        )


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
