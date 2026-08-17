from unittest import mock

from bluebottle.activity_pub.tests.factories import DoGoodEventFactory
from bluebottle.initiatives.tests.factories import (
    InitiativeFactory,
    InitiativePlatformSettingsFactory,
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DateParticipantFactory,
    DateRegistrationFactory,
    DeadlineActivityFactory,
    DeadlineParticipantFactory,
    DeadlineRegistrationFactory,
    PeriodicActivityFactory,
    PeriodicRegistrationFactory,
    ScheduleActivityFactory,
    ScheduleParticipantFactory,
    ScheduleRegistrationFactory,
    TeamFactory,
    TeamScheduleRegistrationFactory,
)


class AdoptedActivityReviewTestCase:
    """
    On a consumer (adopted) activity with review enabled, joining must leave
    both registration and participant in 'new' — not auto-accepted.
    """

    activity_factory = None
    registration_factory = None

    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=[self.activity_factory._meta.model.__name__.lower()]
        )
        self.admin_user = BlueBottleUserFactory.create(is_staff=True)
        self.user = BlueBottleUserFactory.create()
        self.initiative = InitiativeFactory(owner=self.user)

        self.activity = self.activity_factory.create(
            initiative=self.initiative,
            review=True,
            capacity=4,
            registration_deadline=None,
            **self.activity_kwargs
        )
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.activity.states.publish(save=True)

        DoGoodEventFactory.create(adopted=self.activity)
        self.activity.refresh_from_db()
        self.assertTrue(self.activity.is_adopted)

    @property
    def activity_kwargs(self):
        return {}

    def create_registration(self, as_user=None):
        user = BlueBottleUserFactory.create()
        return self.registration_factory.create(
            activity=self.activity,
            user=user,
            as_user=as_user or user,
        )


class DeadlineAdoptedReviewTestCase(AdoptedActivityReviewTestCase, BluebottleTestCase):
    activity_factory = DeadlineActivityFactory
    registration_factory = DeadlineRegistrationFactory

    def test_user_joins_registration_stays_new(self):
        registration = self.create_registration()
        participant = registration.participants.get()

        self.assertEqual(registration.status, 'new')
        self.assertEqual(participant.status, 'new')

    def test_admin_adds_participant_stays_new(self):
        user = BlueBottleUserFactory.create()
        participant = DeadlineParticipantFactory.create(
            activity=self.activity,
            user=user,
            as_user=self.admin_user,
        )

        self.assertEqual(participant.status, 'new')
        self.assertEqual(participant.registration.status, 'new')


class ScheduleAdoptedReviewTestCase(AdoptedActivityReviewTestCase, BluebottleTestCase):
    activity_factory = ScheduleActivityFactory
    registration_factory = ScheduleRegistrationFactory

    def test_user_joins_registration_stays_new(self):
        registration = self.create_registration()
        participant = registration.participants.get()

        self.assertEqual(registration.status, 'new')
        self.assertEqual(participant.status, 'new')

    def test_admin_adds_participant_stays_new(self):
        user = BlueBottleUserFactory.create()
        participant = ScheduleParticipantFactory.create(
            activity=self.activity,
            user=user,
            as_user=self.admin_user,
        )

        self.assertEqual(participant.status, 'new')
        self.assertEqual(participant.registration.status, 'new')


class PeriodicAdoptedReviewTestCase(AdoptedActivityReviewTestCase, BluebottleTestCase):
    activity_factory = PeriodicActivityFactory
    registration_factory = PeriodicRegistrationFactory

    def test_user_joins_registration_stays_new(self):
        registration = self.create_registration()
        participant = registration.participants.get()

        self.assertEqual(registration.status, 'new')
        self.assertEqual(participant.status, 'new')

    def test_admin_adds_registration_stays_new(self):
        registration = self.create_registration(as_user=self.admin_user)
        participant = registration.participants.get()

        self.assertEqual(registration.status, 'new')
        self.assertEqual(participant.status, 'new')


class DateAdoptedReviewTestCase(AdoptedActivityReviewTestCase, BluebottleTestCase):
    activity_factory = DateActivityFactory
    registration_factory = DateRegistrationFactory

    @property
    def activity_kwargs(self):
        return {'slots': []}

    def setUp(self):
        super(AdoptedActivityReviewTestCase, self).setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=[self.activity_factory._meta.model.__name__.lower()]
        )
        self.admin_user = BlueBottleUserFactory.create(is_staff=True)
        self.user = BlueBottleUserFactory.create()
        self.initiative = InitiativeFactory(owner=self.user)

        self.activity = self.activity_factory.create(
            initiative=self.initiative,
            review=True,
            capacity=4,
            registration_deadline=None,
            **self.activity_kwargs
        )
        self.slot = DateActivitySlotFactory.create(
            activity=self.activity,
            is_online=True,
            location=None,
        )
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.activity.states.publish(save=True)

        DoGoodEventFactory.create(adopted=self.activity)
        self.activity.refresh_from_db()
        self.assertTrue(self.activity.is_adopted)

    def test_user_joins_registration_stays_new(self):
        registration = self.create_registration()
        with mock.patch('bluebottle.activity_pub.adapters.adapter.sync'):
            participant = DateParticipantFactory.create(
                activity=self.activity,
                slot=self.slot,
                registration=registration,
                user=registration.user,
                as_user=registration.user,
            )

        registration.refresh_from_db()
        self.assertEqual(registration.status, 'new')
        self.assertEqual(participant.status, 'new')

    def test_admin_adds_participant_stays_new(self):
        user = BlueBottleUserFactory.create()
        with mock.patch('bluebottle.activity_pub.adapters.adapter.sync'):
            participant = DateParticipantFactory.create(
                activity=self.activity,
                slot=self.slot,
                user=user,
                registration=None,
                as_user=self.admin_user,
            )

        self.assertEqual(participant.status, 'new')
        self.assertEqual(participant.registration.status, 'new')


class TeamScheduleAdoptedReviewTestCase(AdoptedActivityReviewTestCase, BluebottleTestCase):
    activity_factory = ScheduleActivityFactory
    registration_factory = TeamScheduleRegistrationFactory

    def setUp(self):
        super().setUp()
        self.activity.team_activity = True
        self.activity.save()

    def test_user_joins_registration_stays_new(self):
        registration = self.create_registration()
        team = TeamFactory.create(
            registration=registration,
            activity=self.activity,
            user=registration.user,
        )
        participant = team.team_members.get().participants.get()

        self.assertEqual(registration.status, 'new')
        self.assertEqual(team.status, 'new')
        self.assertEqual(participant.status, 'new')
