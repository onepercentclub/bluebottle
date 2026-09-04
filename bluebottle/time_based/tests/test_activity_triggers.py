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
    TeamFactory,
    DeadlineActivityFactory,
    DeadlineRegistrationFactory,
    PeriodicActivityFactory, ScheduleActivityFactory, TeamScheduleRegistrationFactory,
    InterestFactory,
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

    def test_change_registration_deadline(self):
        self.publish()

        self.activity.refresh_from_db()

        self.activity.registration_deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, "registration_closed")

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.registration_deadline = date.today() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, "open")

    def test_registration_deadline_today_closes_registration(self):
        self.publish()

        self.activity.refresh_from_db()

        self.activity.registration_deadline = date.today()
        self.activity.save()

        self.assertEqual(self.activity.status, "registration_closed")


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

    def test_registration_closed_reopens_to_full_when_at_capacity(self):
        self.publish()
        self.create_participants()

        self.activity.capacity = len(self.registrations)
        self.activity.save()
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "full")

        self.activity.registration_deadline = date.today() - timedelta(days=1)
        self.activity.save()
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "registration_closed")

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.registration_deadline = date.today() + timedelta(days=1)
        self.activity.save()
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "full")

    def test_withdraw_while_registration_closed_does_not_reopen(self):
        self.publish()
        self.create_participants()

        self.activity.registration_deadline = date.today() - timedelta(days=1)
        self.activity.save()
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "registration_closed")

        participant = self.registrations[0].participants.first()
        participant.states.withdraw(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "registration_closed")

    def test_remove_while_registration_closed_does_not_reopen(self):
        self.publish()
        self.create_participants()

        self.activity.registration_deadline = date.today() - timedelta(days=1)
        self.activity.save()
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "registration_closed")

        participant = self.registrations[0].participants.first()
        participant.states.remove(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "registration_closed")

    def test_capacity_increase_while_registration_closed_does_not_reopen(self):
        self.publish()
        self.create_participants()

        self.activity.capacity = len(self.registrations)
        self.activity.save()
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "full")

        self.activity.registration_deadline = date.today() - timedelta(days=1)
        self.activity.save()
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "registration_closed")

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.capacity = len(self.registrations) + 5
        self.activity.save()
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, "registration_closed")

    def test_extend_deadline_while_registration_closed_does_not_reopen(self):
        self.publish()
        self.create_participants()

        self.activity.registration_deadline = date.today() - timedelta(days=1)
        self.activity.save()
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "registration_closed")

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.deadline = date.today() + timedelta(weeks=8)
        self.activity.save()
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, "registration_closed")

    def test_extend_deadline_from_succeeded_closes_registration_when_still_past(self):
        self.publish()
        self.create_participants()

        self.activity.registration_deadline = date.today() - timedelta(days=1)
        self.activity.save()
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "registration_closed")

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.deadline = date.today() - timedelta(days=1)
        self.activity.save()
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "succeeded")

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.deadline = date.today() + timedelta(weeks=8)
        self.activity.save()
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, "registration_closed")

    def test_change_capacity_notifies_interested(self):
        self.publish()
        self.create_participants()

        interested = BlueBottleUserFactory.create()
        InterestFactory.create(activity=self.activity, user=interested)

        self.activity.capacity = len(self.registrations)
        self.activity.save()
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "full")

        mail.outbox = []
        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.capacity = len(self.registrations) + 1
        self.activity.save()

        self.assertEqual(self.activity.status, "open")
        subjects = [message.subject for message in mail.outbox]
        self.assertIn(
            'A spot has opened up for an activity on Test.',
            subjects,
        )
        self.assertTrue(
            any(interested.email in message.to for message in mail.outbox)
        )

    def test_change_capacity_after_deadline_does_not_notify(self):
        self.publish()
        self.create_participants()

        interested = BlueBottleUserFactory.create()
        InterestFactory.create(activity=self.activity, user=interested)

        self.activity.capacity = len(self.registrations)
        self.activity.save()
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "full")

        mail.outbox = []
        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.registration_deadline = date.today() - timedelta(days=1)
        self.activity.capacity = len(self.registrations) + 1
        self.activity.save()

        subjects = [message.subject for message in mail.outbox]
        self.assertNotIn(
            'A spot has opened up for an activity on Test.',
            subjects,
        )

    def test_second_open_transition_notifies_again(self):
        self.publish()
        self.create_participants()

        interested = BlueBottleUserFactory.create()
        InterestFactory.create(activity=self.activity, user=interested)

        self.activity.capacity = len(self.registrations)
        self.activity.save()
        self.assertEqual(self.activity.status, "full")

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.capacity = len(self.registrations) + 1
        self.activity.save()
        self.assertEqual(self.activity.status, "open")

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.capacity = len(self.registrations)
        self.activity.save()
        self.assertEqual(self.activity.status, "full")

        mail.outbox = []
        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.capacity = len(self.registrations) + 1
        self.activity.save()
        self.assertEqual(self.activity.status, "open")

        subjects = [message.subject for message in mail.outbox]
        self.assertEqual(
            subjects.count('A spot has opened up for an activity on Test.'),
            1,
        )

    def test_change_capacity_while_open_does_not_notify(self):
        self.publish()
        self.create_participants()

        interested = BlueBottleUserFactory.create()
        InterestFactory.create(activity=self.activity, user=interested)

        self.activity.capacity = len(self.registrations)
        self.activity.save()
        self.assertEqual(self.activity.status, "full")

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.capacity = len(self.registrations) + 1
        self.activity.save()
        self.assertEqual(self.activity.status, "open")

        mail.outbox = []
        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.capacity = len(self.registrations) + 2
        self.activity.save()
        self.assertEqual(self.activity.status, "open")

        subjects = [message.subject for message in mail.outbox]
        self.assertNotIn(
            'A spot has opened up for an activity on Test.',
            subjects,
        )

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
        self.team = TeamFactory.create(
            registration=self.registration,
            activity=self.activity,
            user=self.registration.user
        )
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
