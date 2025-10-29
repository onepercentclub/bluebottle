from datetime import date, timedelta

from django.core import mail
from django.utils.timezone import now

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
    PeriodicActivityFactory, ScheduleActivityFactory, TeamScheduleRegistrationFactory,
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


class ScheduleActivityTriggerTestCase(ActivityTriggerTestCase, BluebottleTestCase):
    factory = ScheduleActivityFactory

    def setUp(self):
        super().setUp()
        self.activity.team_activity = 'teams'
        self.activity.save()

    def register_team(self):
        self.registration = TeamScheduleRegistrationFactory.create(activity=self.activity, user=self.user)
        self.team = self.registration.team
        self.team_member = self.team.team_members.first()
        self.slot = self.team.slots.first()
        self.participant = self.slot.participants.first()
        self.contribution = self.participant.contributions.first()
        self.registration.states.accept(save=True)

    def test_succeed_manually(self):
        self.publish()
        self.register_team()
        self.assertEqual(len(self.activity.team_slots.all()), 1)
        self.assertStatus(self.activity, "open")
        self.assertStatus(self.registration, "accepted")
        self.assertStatus(self.team, "accepted")
        self.assertStatus(self.team_member, "active")
        self.assertStatus(self.slot, "new")
        self.assertStatus(self.participant, "accepted")
        self.assertStatus(self.contribution, "new")

        self.activity.states.succeed_manually(save=True)

        self.assertStatus(self.activity, "succeeded")
        self.assertStatus(self.team, "succeeded")
        self.assertStatus(self.team_member, "active")
        self.assertStatus(self.slot, "finished")
        self.assertStatus(self.participant, "succeeded")
        self.assertStatus(self.contribution, "succeeded")

    def test_change_end_date(self):
        self.publish()
        self.register_team()

        self.activity.deadline = date.today() - timedelta(days=10)
        self.activity.save()
        self.assertStatus(self.activity, "succeeded")
        self.assertStatus(self.team, "succeeded")
        self.assertStatus(self.team_member, "active")
        self.assertStatus(self.slot, "finished")
        self.assertStatus(self.participant, "succeeded")
        self.assertStatus(self.contribution, "succeeded")

    def test_schedule_team(self):
        self.publish()
        self.register_team()

        self.slot.start = now() + timedelta(days=1)
        self.slot.save()
        self.assertStatus(self.team, "scheduled")
        self.assertStatus(self.team_member, "active")
        self.assertStatus(self.slot, "scheduled")
        self.assertStatus(self.participant, "scheduled")
        self.assertStatus(self.contribution, "new")

    def test_schedule_team_past(self):
        self.publish()
        self.register_team()

        self.slot.start = now() - timedelta(days=1)
        self.slot.save()
        self.assertStatus(self.team, "succeeded")
        self.assertStatus(self.team_member, "active")
        self.assertStatus(self.slot, "finished")
        self.assertStatus(self.participant, "succeeded")
        self.assertStatus(self.contribution, "succeeded")
