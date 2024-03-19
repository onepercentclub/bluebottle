from django.core import mail

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
        self.registration = self.factory.create(activity=self.activity)

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
        self.factory.create_batch(self.activity.capacity - 1, activity=self.activity)
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

    def test_reopen_reject(self):
        self.test_fill_accept()
        self.registration.states.reject(save=True)
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "open")


class DeadlineRegistationTriggerTestCase(
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
        self.assertEqual(self.registration.status, 'accepted')
        self.assertEqual(self.registration.participants.count(), 1)
        self.assertEqual(self.registration.participants.get().status, "new")

    def test_initial_review(self):
        super().test_initial_review()

        self.assertEqual(self.registration.participants.count(), 0)

    def test_accept(self):
        super().test_accept()
        self.assertEqual(self.registration.participants.count(), 1)
        self.assertEqual(self.registration.participants.get().status, "new")

    def test_withdraw(self):
        self.test_initial()

        self.registration.states.withdraw(save=True)

        self.assertEqual(self.registration.participants.get().status, "withdrawn")

    def test_reapply(self):
        self.test_withdraw()

        self.registration.states.reapply(save=True)

        self.assertEqual(self.registration.participants.get().status, "new")

    def test_reapply_finished_slot(self):
        self.test_withdraw()

        participant = self.registration.participants.get()
        slot = self.activity.slots.get()
        slot.states.start()
        slot.states.finish(save=True)

        participant.refresh_from_db()

        self.registration.states.reapply(save=True)

        participant.refresh_from_db()
        self.assertEqual(participant.status, "succeeded")

    def test_stop(self):
        self.test_initial()
        mail.outbox = []
        self.registration.states.stop(save=True)
        self.assertEqual(self.registration.participants.get().status, "new")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            f'Your contribution to the activity "{self.activity.title}" has been stopped'
        )

    def test_start(self):
        self.test_initial()
        self.registration.states.stop(save=True)
        mail.outbox = []
        self.registration.states.start(save=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            f'Your contribution to the activity "{self.activity.title}" has been restarted'
        )
