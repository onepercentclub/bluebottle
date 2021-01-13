from datetime import timedelta, date

from django.core import mail
from django.utils.timezone import now

from bluebottle.activities.models import Organizer
from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, PeriodActivityFactory,
    DateParticipantFactory, PeriodParticipantFactory,
    DateActivitySlotFactory, SlotParticipantFactory
)


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
        self.activity.refresh_from_db()

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
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

    def test_change_start_after_registration_deadline(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.activity.registration_deadline = date.today() - timedelta(days=4)
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')

        self.activity.registration_deadline = date.today() - timedelta(days=4)
        self.activity.start = date.today() - timedelta(days=2)
        self.activity.save()
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'running')

        self.activity.start = date.today() + timedelta(days=2)
        self.activity.save()
        self.activity.refresh_from_db()

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
        self.activity.refresh_from_db()

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


class DateActivitySlotTriggerTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user)

        self.activity = DateActivityFactory.create(initiative=self.initiative, review=False)
        self.slot = DateActivitySlotFactory.create(activity=self.activity)

        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

    def test_incomplete(self):
        self.slot.start = None
        self.slot.save()
        self.assertEqual(self.slot.status, 'draft')

    def test_complete(self):
        self.test_incomplete()
        self.slot.start = now() + timedelta(days=2)
        self.slot.save()

        self.assertEqual(self.slot.status, 'open')

    def test_start(self):
        self.slot.start = now() - timedelta(hours=1)
        self.slot.save()

        self.assertEqual(self.slot.status, 'running')

    def test_finish(self):
        self.slot.start = now() - timedelta(days=1)
        self.slot.save()

        self.assertEqual(self.slot.status, 'finished')

    def test_reschedule_open(self):
        self.test_finish()
        self.slot.start = now() + timedelta(days=1)
        self.slot.save()

        self.assertEqual(self.slot.status, 'open')

    def test_reschedule_running(self):
        self.test_finish()
        self.slot.start = now() - timedelta(hours=1)
        self.slot.save()

        self.assertEqual(self.slot.status, 'running')


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


class AllSlotParticipantTriggerTestCase(BluebottleTestCase):

    def setUp(self):
        self.user = BlueBottleUserFactory.create()
        self.initiative = InitiativeFactory.create()
        self.activity = DateActivityFactory.create(
            slots=[],
            capacity=True,
            slot_selection='all',
            initiative=self.initiative
        )
        self.slot1 = DateActivitySlotFactory.create(activity=self.activity)
        self.slot2 = DateActivitySlotFactory.create(activity=self.activity)
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)
        self.activity.refresh_from_db()
        self.participant = DateParticipantFactory.create(
            activity=self.activity
        )
        self.slot1_participant = self.participant.slot_participants.filter(slot=self.slot1).first()
        self.slot2_participant = self.participant.slot_participants.filter(slot=self.slot2).first()
        self.contribution1 = self.slot1_participant.contributions.first()
        self.contribution2 = self.slot2_participant.contributions.first()

    def assertStatus(self, obj, status):
        obj.refresh_from_db()
        self.assertEqual(obj.status, status)

    def test_apply(self):
        self.assertStatus(self.slot1_participant, 'registered')
        self.assertStatus(self.contribution1, 'new')
        self.assertStatus(self.slot2_participant, 'registered')
        self.assertStatus(self.contribution2, 'new')

    def test_remove_participant(self):
        self.participant.states.remove(save=True)
        self.assertStatus(self.slot1_participant, 'registered')
        self.assertStatus(self.contribution1, 'failed')
        self.assertStatus(self.slot2_participant, 'registered')
        self.assertStatus(self.contribution2, 'failed')

    def test_remove_participant_from_slot(self):
        self.slot1_participant.states.remove(save=True)
        self.assertEqual(self.slot1_participant.status, 'removed')
        self.assertStatus(self.contribution1, 'failed')

    def test_withdraw_from_slot(self):
        self.slot1_participant.states.withdraw(save=True)
        self.assertStatus(self.slot1_participant, 'withdrawn')
        self.assertStatus(self.contribution1, 'failed')

    def test_cancel_slot(self):
        self.slot1.states.cancel(save=True)
        self.assertStatus(self.slot1_participant, 'registered')
        self.assertStatus(self.contribution1, 'failed')

    def test_finish_slot(self):
        self.slot1.states.finish(save=True)
        self.assertStatus(self.slot1_participant, 'registered')
        self.assertStatus(self.contribution1, 'succeeded')

    def test_reschedule_slot(self):
        self.slot1.states.finish(save=True)
        self.assertStatus(self.slot1_participant, 'registered')
        self.assertStatus(self.contribution1, 'succeeded')
        self.slot1.states.reschedule(save=True)
        self.assertStatus(self.slot1_participant, 'registered')
        self.assertStatus(self.contribution1, 'new')

    def test_cancel_activity(self):
        self.activity.states.cancel(save=True)
        self.assertStatus(self.slot1_participant, 'registered')
        self.assertStatus(self.contribution1, 'failed')


class FreeSlotParticipantTriggerTestCase(BluebottleTestCase):

    def setUp(self):
        self.user = BlueBottleUserFactory.create()
        self.initiative = InitiativeFactory.create()
        self.activity = DateActivityFactory.create(
            slots=[],
            capacity=True,
            slot_selection='free',
            initiative=self.initiative
        )
        self.slot1 = DateActivitySlotFactory.create(
            activity=self.activity,
            capacity=2
        )
        self.slot2 = DateActivitySlotFactory.create(
            activity=self.activity,
            capacity=1
        )

        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)
        self.activity.refresh_from_db()
        self.participant = DateParticipantFactory.create(activity=self.activity)

    def assertStatus(self, obj, status):
        obj.refresh_from_db()
        self.assertEqual(obj.status, status)

    def test_apply(self):
        self.assertEqual(
            self.participant.slot_participants.count(),
            0
        )
        slot_participant = SlotParticipantFactory.create(slot=self.slot1, participant=self.participant)
        self.assertEqual(
            self.participant.slot_participants.count(),
            1
        )
        self.assertStatus(slot_participant, 'registered')

    def test_withdraw_from_slot(self):
        slot_participant = SlotParticipantFactory.create(slot=self.slot1, participant=self.participant)
        slot_participant.states.withdraw(save=True)
        self.assertStatus(slot_participant, 'withdrawn')

    def test_fill_slot(self):
        SlotParticipantFactory.create(slot=self.slot1, participant=self.participant)
        self.assertStatus(self.slot1, 'open')
        SlotParticipantFactory.create(slot=self.slot1, participant=self.participant)
        self.assertStatus(self.slot1, 'full')
        SlotParticipantFactory.create(slot=self.slot2, participant=self.participant)
        self.assertStatus(self.slot2, 'full')

    def test_unfill_slot(self):
        slot_part = SlotParticipantFactory.create(slot=self.slot2, participant=self.participant)
        self.assertStatus(self.slot2, 'full')
        slot_part.states.withdraw(save=True)
        self.assertStatus(self.slot2, 'open')
