from datetime import date, timedelta

from django.core import mail

from bluebottle.activities.models import Organizer
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
)


class ActivityTriggerTestCase:
    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=[self.factory._meta.model.__name__.lower()]
        )

        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user)

        self.activity = self.factory.create(
            initiative=self.initiative,
            review=False,
            capacity=4,
            registration_deadline=None,
        )

    def publish(self):
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.activity.states.publish(save=True)

    def test_initial(self):
        organizer = self.activity.contributors.instance_of(Organizer).get()
        self.assertEqual(organizer.status, "new")

    def test_submit_initiative(self):
        self.initiative.states.submit(save=True)
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, "submitted")

    def test_approve_initiative(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, "open")

        organizer = self.activity.contributors.instance_of(Organizer).get()
        self.assertEqual(organizer.status, "succeeded")

    def test_submit_initiative_already_approved(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        activity = self.factory.create(initiative=self.initiative)
        activity.states.publish(save=True)

        self.assertEqual(activity.status, "open")

    def test_delete(self):
        self.activity.states.delete(save=True)
        organizer = self.activity.contributors.instance_of(Organizer).get()
        self.assertEqual(organizer.status, "failed")

    def test_reject(self):
        self.activity.states.reject(save=True)

        organizer = self.activity.contributors.instance_of(Organizer).get()
        self.assertEqual(organizer.status, "failed")

        self.assertEqual(
            mail.outbox[-1].subject,
            'Your activity "{}" has been rejected'.format(self.activity.title),
        )

    def test_cancel(self):
        self.publish()
        self.activity.states.cancel(save=True)

        self.assertEqual(self.activity.status, "cancelled")

        organizer = self.activity.contributors.instance_of(Organizer).get()
        self.assertEqual(organizer.status, "failed")

        self.assertEqual(
            mail.outbox[-1].subject,
            'Your activity "{}" has been cancelled'.format(self.activity.title),
        )

    def change_registration_deadline(self):
        self.publish()

        self.activity.refresh_from_db()

        self.activity.registration_deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, "full")

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.registration_deadline = date.today() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, "open")


class DeadlineActivityTriggerTestCase(ActivityTriggerTestCase, BluebottleTestCase):
    factory = DeadlineActivityFactory

    def create_participants(self):
        user1 = BlueBottleUserFactory()
        user2 = BlueBottleUserFactory()
        self.registrations = [
            DeadlineRegistrationFactory.create(
                activity=self.activity,
                user=user1,
                as_user=user1
            ),
            DeadlineRegistrationFactory.create(
                activity=self.activity,
                user=user2,
                as_user=user2
            )
        ]

    def test_change_capacity(self):
        self.publish()
        self.create_participants()

        self.activity.capacity = len(self.registrations)
        self.activity.save()
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, "full")

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.capacity = len(self.registrations) + 1
        self.activity.save()

        self.assertEqual(self.activity.status, "open")

    def test_reject(self):
        self.publish()
        self.create_participants()

        super().test_reject()

        for registration in self.registrations:
            self.assertEqual(registration.participants.first().status, "cancelled")

    def test_restore(self):
        self.test_reject()
        self.activity.states.restore(save=True)

        for registration in self.registrations:
            self.assertEqual(registration.participants.first().status, "succeeded")

    def test_cancel(self):
        self.create_participants()
        super().test_cancel()
        for registration in self.registrations:
            self.assertEqual(registration.participants.first().status, "cancelled")


class PeriodicActivityTriggerTestCase(ActivityTriggerTestCase, BluebottleTestCase):
    factory = PeriodicActivityFactory

    def test_initial(self):
        super().test_initial()
        self.assertEqual(len(self.activity.slots.all()), 0)

    def test_publish(self):
        self.publish()
        self.assertEqual(len(self.activity.slots.all()), 1)
