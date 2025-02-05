from datetime import timedelta

from django.core import mail
from django.utils.timezone import now

from bluebottle.initiatives.tests.factories import (
    InitiativeFactory,
    InitiativePlatformSettingsFactory,
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import (
    DeadlineActivityFactory,
    DeadlineRegistrationFactory,
    PeriodicActivityFactory,
    PeriodicRegistrationFactory,
    ScheduleActivityFactory,
    ScheduleRegistrationFactory,
    TeamScheduleRegistrationFactory, DateActivityFactory, DateRegistrationFactory, DateParticipantFactory,
    DateActivitySlotFactory,
)


class RegistrationTriggerTestCase:
    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=[self.activity_factory._meta.model.__name__.lower()]
        )

        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user)

        self.activity = self.activity_factory.create(
            initiative=self.initiative,
            review=False,
            capacity=4,
            registration_deadline=None,
        )
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.activity.states.publish(save=True)

        mail.outbox = []

    def create(self):
        self.registration = self.factory.create(
            activity=self.activity,
            user=self.user,
            as_user=self.user,
        )

    def test_initial(self):
        self.create()
        self.assertEqual(self.registration.status, "accepted")

        self.assertEqual(
            mail.outbox[-2].subject,
            'You have a new participant for your activity "{}" 🎉'.format(
                self.activity.title
            ),
        )
        self.assertEqual(
            mail.outbox[-1].subject,
            'You have joined the activity "{}"'.format(self.activity.title),
        )

    def test_initial_review(self):
        self.activity.review = True
        self.activity.save()

        self.create()
        self.assertEqual(self.registration.status, "new")
        self.assertEqual(
            len(mail.outbox),
            2,
        )

        self.assertEqual(
            mail.outbox[-2].subject,
            f'You have a new application for your activity "{self.activity.title}" 🎉',
        )
        self.assertEqual(
            mail.outbox[-1].subject,
            f'You have applied to the activity "{self.activity.title}"',
        )

    def test_accept(self):
        self.test_initial_review()
        self.registration.states.accept(save=True)

        self.assertEqual(
            mail.outbox[-1].subject,
            'You have been selected for the activity "{}"'.format(self.activity.title),
        )

    def test_fill(self):
        self.factory.create_batch(
            self.activity.capacity - 1,
            activity=self.activity,
            user=BlueBottleUserFactory(),
            as_relation='user'
        )
        self.create()
        self.assertEqual(self.registration.status, "accepted")
        self.assertEqual(self.registration.activity.status, "full")

    def test_fill_accept(self):
        self.activity.review = True
        self.activity.save()

        for registration in self.factory.create_batch(
            self.activity.capacity - 1, activity=self.activity
        ):
            registration.states.accept(save=True)

        self.create()
        self.registration.states.accept(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "full")

    def test_reject(self):
        self.activity.review = True
        self.activity.save()

        self.create()
        self.registration.states.reject(save=True)

        self.assertEqual(
            mail.outbox[-1].subject,
            'You have not been selected for the activity "{}"'.format(
                self.activity.title
            ),
        )


class DateRegistrationTriggerTestCase(
    RegistrationTriggerTestCase, BluebottleTestCase
):
    activity_factory = DateActivityFactory
    factory = DateRegistrationFactory

    def create(self):
        self.registration = self.factory.create(
            activity=self.activity,
            user=self.user,
            as_user=self.user,
        )
        self.slot = DateActivitySlotFactory.create(
            activity=self.activity
        )
        self.participant = DateParticipantFactory.create(
            registration=self.registration,
            slot=self.slot,
        )

    def test_initial(self):
        super().test_initial()
        self.assertEqual(self.registration.participants.count(), 1)
        self.assertStatus(self.registration, "accepted")
        self.assertStatus(self.participant, "registered")

    def test_initial_review(self):
        super().test_initial_review()
        self.assertEqual(self.registration.participants.count(), 1)
        self.assertStatus(self.registration, "new")
        self.assertStatus(self.participant, "registered")

    def test_initial_past(self):
        super().test_initial()
        self.slot.start = now() - timedelta(days=3)
        self.slot.save()
        self.assertEqual(self.registration.participants.count(), 1)
        self.assertStatus(self.registration, "accepted")
        self.assertStatus(self.participant, "accepted")

    def test_initial_review_past(self):
        super().test_initial_review()
        self.slot.start = now() - timedelta(days=3)
        self.slot.save()
        self.assertEqual(self.registration.participants.count(), 1)
        self.assertStatus(self.registration, "new")
        self.assertStatus(self.participant, "registered")

    def test_accept(self):
        super().test_accept()
        self.slot.start = now() - timedelta(days=3)
        self.slot.save()
        self.assertStatus(self.registration, "accepted")
        self.assertStatus(self.participant, "succeeded")

    def test_reject(self):
        super().test_reject()
        self.assertStatus(self.registration, "rejected")
        self.assertStatus(self.participant, "rejected")

    def test_fill(self):
        super().test_initial_review()
        self.slot.capacity = 1
        self.slot.save()
        self.registration.states.accept(save=True)

        self.assertStatus(self.registration, "accepted")
        self.assertStatus(self.participant, "accepted")
        self.assertStatus(self.slot, "full")

    def test_reject_then_accept(self):
        super().test_reject()
        self.registration.states.accept(save=True)

        self.assertEqual(self.registration.participants.get().status, "succeeded")


class DeadlineRegistrationTriggerTestCase(
    RegistrationTriggerTestCase, BluebottleTestCase
):
    activity_factory = DeadlineActivityFactory
    factory = DeadlineRegistrationFactory

    def test_initial(self):
        super().test_initial()
        self.assertEqual(len(self.registration.participants.all()), 1)

        participant = self.registration.participants.get()
        self.assertEqual(participant.status, "succeeded")

    def test_initial_review(self):
        super().test_initial_review()
        self.assertEqual(len(self.registration.participants.all()), 1)
        self.assertEqual(self.registration.participants.get().status, "new")

    def test_accept(self):
        super().test_accept()
        self.assertEqual(self.registration.participants.get().status, "succeeded")

    def test_reject(self):
        super().test_reject()
        self.assertEqual(self.registration.participants.get().status, "rejected")

    def test_reject_then_accept(self):
        super().test_reject()
        self.registration.states.accept(save=True)

        self.assertEqual(self.registration.participants.get().status, "succeeded")


class PeriodicRegistrationTriggerTestCase(
    RegistrationTriggerTestCase, BluebottleTestCase
):
    activity_factory = PeriodicActivityFactory
    factory = PeriodicRegistrationFactory

    def test_initial(self):
        super().test_initial()
        self.assertEqual(self.registration.status, "accepted")
        self.assertEqual(self.registration.participants.count(), 1)
        self.assertEqual(self.registration.participants.get().status, "new")

    def test_initial_review(self):
        super().test_initial_review()
        self.assertEqual(self.registration.participants.count(), 1)
        self.assertEqual(self.registration.participants.get().status, "new")

    def test_accept(self):
        super().test_accept()
        self.assertEqual(self.registration.participants.count(), 1)
        self.assertEqual(self.registration.participants.get().status, "accepted")

    def test_remove(self):
        self.test_accept()

        mail.outbox = []

        self.registration.states.remove(save=True)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            f'You have been removed from the activity "{self.activity.title}"'
        )

        self.assertEqual(self.registration.participants.count(), 1)
        self.assertEqual(self.registration.participants.get().status, "removed")

    def test_stop(self):
        self.test_initial()
        mail.outbox = []
        self.registration.states.stop(save=True)
        self.assertEqual(self.registration.participants.get().status, "new")
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            f'Your contribution to the activity "{self.activity.title}" has been stopped',
        )
        self.assertEqual(
            mail.outbox[1].subject,
            f'A participant for your activity "{self.activity.title}" has stopped',
        )

    def test_unfill_stop(self):
        self.test_fill()
        self.registration.states.stop(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "open")

    def test_start(self):
        self.test_initial()
        self.registration.states.stop(save=True)
        mail.outbox = []
        self.registration.states.start(save=True)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            f'Your contribution to the activity "{self.activity.title}" has been restarted',
        )
        self.assertEqual(
            mail.outbox[1].subject,
            f'A participant for your activity "{self.activity.title}" has restarted',
        )

    def test_fill_start(self):
        self.test_fill()
        self.registration.states.stop(save=True)
        self.registration.states.start(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "full")


class ScheduleRegistationTriggerTestCase(
    RegistrationTriggerTestCase, BluebottleTestCase
):
    activity_factory = ScheduleActivityFactory
    factory = ScheduleRegistrationFactory

    def test_initial(self):
        super().test_initial()
        self.assertEqual(len(self.registration.participants.all()), 1)

        participant = self.registration.participants.get()
        self.assertEqual(participant.status, "accepted")

    def test_initial_review(self):
        super().test_initial_review()
        self.assertEqual(len(self.registration.participants.all()), 1)
        self.assertEqual(self.registration.participants.get().status, "new")

    def test_accept(self):
        super().test_accept()
        self.assertEqual(self.registration.participants.get().status, "accepted")

    def test_reject(self):
        super().test_reject()
        self.assertEqual(self.registration.participants.get().status, "rejected")

    def test_reject_then_accept(self):
        super().test_reject()
        self.registration.states.accept(save=True)

        self.assertEqual(self.registration.participants.get().status, "accepted")


class TeamScheduleRegistrationTriggerTestCase(
    RegistrationTriggerTestCase, BluebottleTestCase
):
    activity_factory = ScheduleActivityFactory
    factory = TeamScheduleRegistrationFactory

    def setUp(self):
        super().setUp()
        self.activity.team_activity = True
        self.activity.save()

    def create(self):
        self.registration = self.factory.create(
            activity=self.activity,
            user=self.user,
            as_user=self.user,
        )

    def test_initial(self):
        self.create()
        self.assertEqual(self.registration.status, "accepted")
        self.assertEqual(self.registration.team.status, "accepted")
        self.assertEqual(self.registration.team.team_members.get().status, "active")
        self.assertEqual(
            self.registration.team.team_members.get().participants.get().status,
            "accepted",
        )

        self.assertEqual(len(mail.outbox), 2)

        self.assertEqual(
            mail.outbox[0].subject,
            'You have a new team for your activity "{}" 🎉'.format(self.activity.title),
        )
        self.assertEqual(
            mail.outbox[1].subject,
            'You have registered your team on "Test"',
        )

    def test_initial_review(self):
        self.activity.review = True
        self.activity.save()

        self.create()
        self.assertEqual(self.registration.status, "new")

        self.assertEqual(len(mail.outbox), 2)

        self.assertEqual(
            mail.outbox[0].subject,
            f'A new team has applied to your activity "{self.activity.title}" 🎉',
        )
        self.assertEqual(
            mail.outbox[1].subject,
            'You have registered your team on "Test"'
        )
        self.assertEqual(self.registration.team.status, "new")
        self.assertEqual(self.registration.team.team_members.get().status, "active")
        self.assertEqual(
            self.registration.team.team_members.get().participants.get().status, "new"
        )

    def test_reject(self):
        self.activity.review = True
        self.activity.save()

        self.create()
        self.registration.states.reject(save=True)

        self.assertEqual(
            mail.outbox[-1].subject,
            'Your team has not been selected for the activity "{}"'.format(
                self.activity.title
            ),
        )

        self.assertEqual(self.registration.team.status, "rejected")
        self.assertEqual(self.registration.team.team_members.get().status, "rejected")

        self.assertEqual(
            self.registration.team.team_members.get().participants.get().status,
            "rejected",
        )

    def test_accept(self):
        self.test_initial_review()
        self.registration.states.accept(save=True)

        self.assertEqual(
            mail.outbox[-1].subject,
            'Your team has been selected for the activity "{}"'.format(
                self.activity.title
            ),
        )

        self.assertEqual(self.registration.team.status, "accepted")
        self.assertEqual(self.registration.team.team_members.get().status, "active")

        self.assertEqual(
            self.registration.team.team_members.get().participants.get().status,
            "accepted",
        )
