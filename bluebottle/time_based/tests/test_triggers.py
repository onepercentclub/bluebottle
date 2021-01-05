from datetime import timedelta, date

from django.core import mail
from django.utils.timezone import now

from bluebottle.time_based.tests.factories import (
    DateActivityFactory, PeriodActivityFactory,
    DateParticipantFactory, PeriodParticipantFactory
)
from bluebottle.activities.models import Organizer
from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class TimeBasedActivityTriggerTestCase():
    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=[self.factory._meta.model.__name__.lower()]
        )

        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user)

        self.activity = self.factory.create(initiative=self.initiative, review=False)

    def test_initial(self):
        organizer = self.activity.contributors.instance_of(Organizer).get()
        self.assertEqual(organizer.status, 'new')

    def test_delete(self):
        self.activity.states.delete(save=True)
        organizer = self.activity.contributors.instance_of(Organizer).get()
        self.assertEqual(organizer.status, 'failed')

    def test_reject(self):
        self.initiative.states.submit(save=True)
        self.activity.states.submit()
        self.activity.states.reject(save=True)
        organizer = self.activity.contributors.instance_of(Organizer).get()
        self.assertEqual(organizer.status, 'failed')

        self.assertEqual(
            mail.outbox[-1].subject,
            'Your activity "{}" has been rejected'.format(self.activity.title)
        )

    def test_submit_initiative(self):
        self.initiative.states.submit(save=True)
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'submitted')

    def test_submit_initiative_already_approved(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        activity = self.factory.create(initiative=self.initiative)
        activity.states.submit(save=True)

        self.assertEqual(activity.status, 'open')

    def test_submit_initiative_not_approved(self):
        self.initiative.states.submit(save=True)

        activity = self.factory.create(initiative=self.initiative)
        activity.states.submit(save=True)

        self.assertEqual(activity.status, 'submitted')

    def test_approve_initiative(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

        organizer = self.activity.contributors.instance_of(Organizer).get()
        self.assertEqual(organizer.status, 'succeeded')

    def test_cancel(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)
        self.activity.refresh_from_db()
        self.activity.states.cancel(save=True)

        self.assertEqual(self.activity.status, 'cancelled')

        organizer = self.activity.contributors.instance_of(Organizer).get()
        self.assertEqual(organizer.status, 'failed')

        self.assertEqual(
            mail.outbox[-1].subject,
            'Your activity "{}" has been cancelled'.format(self.activity.title)
        )

    def test_change_capacity(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.participant_factory.create_batch(
            self.activity.capacity - 1,
            activity=self.activity,
            status='accepted'
        )

        self.activity.capacity = self.activity.capacity - 1
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.capacity = self.activity.capacity + 1
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

    def change_registration_deadline(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.activity.registration_deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.registration_deadline = date.today() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')


class DateActivityTriggerTestCase(TimeBasedActivityTriggerTestCase, BluebottleTestCase):
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory

    def test_reopen(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

        self.activity.start = now() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'expired')
        self.activity.states.reopen_manually(save=True)
        self.assertEqual(self.activity.status, 'draft')
        self.assertIsNone(self.activity.start)

    def test_change_start(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

        self.activity.start = now() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'expired')
        self.assertEqual(
            mail.outbox[-1].subject,
            'The registration deadline for your activity "{}" has expired'.format(self.activity.title)
        )

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.start = now() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

    def test_change_start_future(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

        self.accepted = self.participant_factory.create(
            activity=self.activity,
        )

        self.activity.start = now() + timedelta(days=100)
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')
        self.assertEqual(
            mail.outbox[-1].subject,
            'The date and time for your activity "{}" has changed'.format(self.activity.title)
        )

    def test_change_start_with_contributors(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.accepted = self.participant_factory.create(
            activity=self.activity,
        )

        self.rejected = self.participant_factory.create(
            activity=self.activity,
        )
        self.rejected.states.remove(save=True)

        self.assertEqual(self.activity.status, 'open')

        self.activity.start = now() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'succeeded')
        self.assertEqual(
            mail.outbox[-1].subject,
            'Your activity "{}" has succeeded 🎉'.format(self.activity.title)
        )

        self.assertEqual(
            self.rejected.contributions.get().status, 'failed'
        )

        self.assertEqual(
            self.accepted.contributions.get().status, 'succeeded'
        )

    def test_change_start_back_again(self):
        self.test_change_start_with_contributors()

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.start = now() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

        self.assertEqual(
            self.rejected.contributions.get().status, 'failed'
        )

        self.assertEqual(
            self.accepted.contributions.get().status, 'new'
        )

    def test_change_start_full(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.participant_factory.create_batch(
            self.activity.capacity,
            activity=self.activity,
        )

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')

        self.activity.start = now() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'succeeded')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.start = now() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')


class PeriodActivityTriggerTestCase(TimeBasedActivityTriggerTestCase, BluebottleTestCase):
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory

    def test_reopen(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

        self.activity.deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'expired')
        self.activity.states.reopen_manually(save=True)
        self.assertEqual(self.activity.status, 'draft')
        self.assertIsNone(self.activity.deadline)

    def test_change_deadline(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

        self.activity.deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'expired')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.deadline = date.today() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

    def test_change_deadline_future(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.participant_factory.create(
            activity=self.activity,
            status='accepted'
        )
        self.assertEqual(self.activity.status, 'open')

        self.activity.deadline = date.today() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

    def test_change_deadline_with_contributors(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.participant_factory.create(
            activity=self.activity,
        )
        self.assertEqual(self.activity.status, 'open')

        self.activity.deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'succeeded')

        for duration in self.activity.durations:
            self.assertEqual(duration.status, 'succeeded')

    def test_change_deadline_with_contributors_reopen(self):
        self.test_change_deadline_with_contributors()

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.deadline = date.today() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

    def test_change_deadline_with_contributors_cancel(self):
        self.test_change_deadline_with_contributors()
        self.activity.states.cancel(save=True)

        self.assertEqual(self.activity.status, 'cancelled')

        for duration in self.activity.durations:
            self.assertEqual(duration.status, 'failed')

    def test_change_deadline_full(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.participant_factory.create_batch(
            self.activity.capacity,
            activity=self.activity,
        )

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')

        self.activity.deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'succeeded')

        self.assertEqual(
            mail.outbox[-1].subject,
            'Your activity "{}" has succeeded 🎉'.format(self.activity.title)
        )
        self.assertFalse(
            (
                'Head over to your activity page and enter the impact your activity made, '
                'so that everybody can see how effective your activity was'
            ) in mail.outbox[-1].body
        )

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.deadline = date.today() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')

    def test_change_deadline_full_enable_impact(self):
        InitiativePlatformSettingsFactory.create(enable_impact=True)
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.participant_factory.create_batch(
            self.activity.capacity,
            activity=self.activity,
        )

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')

        self.activity.deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'succeeded')

        self.assertEqual(
            mail.outbox[-1].subject,
            'Your activity "{}" has succeeded 🎉'.format(self.activity.title)
        )
        self.assertTrue(
            (
                'Head over to your activity page and enter the impact your activity made, '
                'so that everybody can see how effective your activity was'
            ) in mail.outbox[-1].body
        )

    def test_change_start(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.activity.start = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'running')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.start = date.today() + timedelta(days=2)
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

    def test_change_start_after_registration_deadline(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.activity.registration_deadline = date.today() - timedelta(days=4)
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.start = date.today() - timedelta(days=1)

        self.activity.save()

        self.assertEqual(self.activity.status, 'running')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.start = date.today() + timedelta(days=2)
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')

    def test_change_start_after_full(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.participant_factory.create_batch(
            self.activity.capacity,
            activity=self.activity,
        )

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'full')

        self.activity.start = date.today() - timedelta(days=1)

        self.activity.save()

        self.assertEqual(self.activity.status, 'running')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.start = date.today() + timedelta(days=2)
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')

    def test_succeed_manually(self):
        self.activity.duration_period = 'weeks'
        self.activity.save()

        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.participant_factory.create_batch(
            self.activity.capacity,
            activity=self.activity,
        )

        self.activity.refresh_from_db()

        self.activity.states.succeed_manually(save=True)
        self.assertEqual(self.activity.deadline, date.today())

        for duration in self.activity.durations:
            self.assertEqual(duration.status, 'succeeded')

        for message in mail.outbox[-self.activity.capacity:]:
            self.assertEqual(
                message.subject,
                'The activity "{}" has succeeded 🎉'.format(self.activity.title)
            )

    def test_succeed_manually_review_new(self):
        self.activity.duration_period = 'weeks'
        self.activity.save()

        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()
        self.activity.review = True
        self.activity.save()

        self.participant_factory.create_batch(
            self.activity.capacity,
            activity=self.activity,
        )

        self.activity.refresh_from_db()
        mail.outbox = []

        self.activity.states.succeed_manually(save=True)
        self.assertEqual(self.activity.deadline, date.today())

        for duration in self.activity.durations:
            self.assertEqual(duration.status, 'succeeded')

        for message in mail.outbox[-self.activity.capacity:]:
            self.assertEqual(
                message.subject,
                'The activity "{}" has succeeded 🎉'.format(self.activity.title)
            )


class ParticipantTriggerTestCase():

    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=[self.factory._meta.model.__name__.lower()]
        )

        self.user = BlueBottleUserFactory()
        self.admin_user = BlueBottleUserFactory(is_staff=True)
        self.initiative = InitiativeFactory(owner=self.user)

        self.activity = self.factory.create(initiative=self.initiative, review=False)
        self.review_activity = self.factory.create(initiative=self.initiative, review=True)

        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()
        self.review_activity.refresh_from_db()

    def test_initial_added_through_admin(self):
        mail.outbox = []
        participant = self.participant_factory.build(
            activity=self.review_activity
        )
        participant.user.save()
        participant.execute_triggers(user=self.admin_user, send_messages=True)
        participant.save()

        self.assertEqual(participant.status, 'accepted')
        self.assertEqual(
            mail.outbox[0].subject,
            'You have been added to the activity "{}" 🎉'.format(self.review_activity.title)
        )
        self.assertTrue(self.review_activity.followers.filter(user=participant.user).exists())

    def test_accept(self):
        participant = self.participant_factory.create(
            activity=self.review_activity,
            status='new'
        )

        mail.outbox = []
        participant.states.accept(save=True)

        self.assertEqual(participant.status, 'accepted')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'You have been selected for the activity "{}" 🎉'.format(
                self.review_activity.title
            )
        )

    def test_initial_review(self):
        mail.outbox = []
        participant = self.participant_factory.build(
            activity=self.review_activity
        )
        participant.user.save()
        participant.execute_triggers(user=participant.user, send_messages=True)
        participant.save()

        self.assertEqual(participant.status, 'new')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'You have a new participant for your activity "{}" 🎉'.format(
                self.review_activity.title
            )
        )
        self.assertTrue(self.review_activity.followers.filter(user=participant.user).exists())
        self.assertEqual(
            participant.contributions.get().status,
            'new'
        )

    def test_initial_no_review(self):
        mail.outbox = []
        participant = self.participant_factory.build(
            activity=self.activity
        )
        participant.user.save()
        participant.execute_triggers(user=participant.user, send_messages=True)
        participant.save()

        self.assertEqual(participant.status, 'accepted')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'A new participant has joined your activity "{}" 🎉'.format(self.activity.title)
        )
        self.assertTrue(self.activity.followers.filter(user=participant.user).exists())
        self.assertEqual(
            self.activity.accepted_participants.get().contributions.get().status,
            'new'
        )

    def test_no_review_fill(self):
        self.participant_factory.create_batch(
            self.activity.capacity, activity=self.activity
        )
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')

    def test_no_review_fill_cancel(self):
        self.participant_factory.create_batch(
            self.activity.capacity, activity=self.activity
        )
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')
        self.activity.states.cancel(save=True)

        self.assertEqual(self.activity.status, 'cancelled')

    def test_review_fill(self):
        participants = self.participant_factory.build_batch(
            self.review_activity.capacity, activity=self.review_activity
        )
        self.review_activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

        for participant in participants:
            participant.user.save()
            participant.execute_triggers(user=participant.user, send_messages=True)
            participant.save()
            participant.states.accept(save=True)

        self.review_activity.refresh_from_db()

        self.assertEqual(self.review_activity.status, 'full')

    def test_remove(self):
        self.participants = self.participant_factory.create_batch(
            self.activity.capacity, activity=self.activity
        )
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')
        mail.outbox = []
        self.participants[0].states.remove(save=True)

        self.assertEqual(
            self.participants[0].contributions.get().status,
            'failed'
        )

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'open')

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'You have been removed as participant for the activity "{}"'.format(
                self.activity.title
            )
        )
        self.assertFalse(self.activity.followers.filter(user=self.participants[0].user).exists())

    def test_reject(self):
        self.participants = self.participant_factory.create_batch(
            self.activity.capacity, activity=self.review_activity
        )

        mail.outbox = []
        self.participants[0].states.reject(save=True)

        self.assertEqual(
            self.participants[0].contributions.get().status,
            'failed'
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'You have not been selected for the activity "{}"'.format(
                self.review_activity.title
            )
        )
        self.assertFalse(self.review_activity.followers.filter(user=self.participants[0].user).exists())

    def test_reaccept(self):
        self.test_remove()

        self.participants[0].states.accept(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'full')

        self.assertEqual(
            self.participants[0].contributions.get().status,
            'new'
        )
        self.assertTrue(self.activity.followers.filter(user=self.participants[0].user).exists())

    def test_withdraw(self):
        self.participants = self.participant_factory.create_batch(
            self.activity.capacity, activity=self.activity
        )
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')

        self.participants[0].states.withdraw(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'open')

        self.assertEqual(
            self.participants[0].contributions.get().status,
            'failed'
        )

        self.assertFalse(self.activity.followers.filter(user=self.participants[0].user).exists())

    def test_reapply(self):
        self.test_withdraw()

        self.participants[0].states.reapply(save=True)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')
        self.assertEqual(
            self.participants[0].contributions.get().status,
            'new'
        )
        self.assertTrue(self.activity.followers.filter(user=self.participants[0].user).exists())


class DateParticipantTriggerTestCase(ParticipantTriggerTestCase, BluebottleTestCase):
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory

    def test_no_review_succeed_after_cancel(self):
        self.activity.start = now() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'expired')

        participant = self.participant_factory.create(activity=self.activity)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'succeeded')
        self.assertEqual(
            participant.contributions.get().status,
            'succeeded'
        )


class PeriodParticipantTriggerTestCase(ParticipantTriggerTestCase, BluebottleTestCase):
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory

    def test_no_review_succeed(self):
        self.activity.deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'expired')

        participant = self.participant_factory.create(activity=self.activity)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'succeeded')

        self.assertEqual(
            participant.contributions.get().status,
            'succeeded'
        )
