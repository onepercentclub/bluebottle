from datetime import timedelta, date, time

import mock
from django.core import mail
from django.template import defaultfilters
from django.utils.timezone import now, get_current_timezone
from tenant_extras.utils import TenantLanguage

from bluebottle.activities.messages import TeamMemberRemovedMessage
from bluebottle.activities.models import Organizer, Activity
from bluebottle.activities.tests.factories import TeamFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, CeleryTestCase, TriggerTestCase
from bluebottle.time_based.messages import (
    ParticipantJoinedNotification, ParticipantChangedNotification,
    ParticipantAppliedNotification, ParticipantRemovedNotification, ParticipantRemovedOwnerNotification,
    NewParticipantNotification, TeamParticipantJoinedNotification, ParticipantAddedNotification,
    ParticipantAddedOwnerNotification, TeamSlotChangedNotification
)
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, PeriodActivityFactory,
    DateParticipantFactory, PeriodParticipantFactory,
    DateActivitySlotFactory, SlotParticipantFactory, TeamSlotFactory
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

    def test_unset_capacity(self):
        self.activity.slot_selection = 'free'
        self.activity.save()

        self.activity.refresh_from_db()
        self.assertIsNone(self.activity.capacity)

    def test_unset_registration_deadline(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.activity.registration_deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.refresh_from_db()
        self.activity.registration_deadline = None
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')


class PeriodActivityTriggerTestCase(TimeBasedActivityTriggerTestCase, BluebottleTestCase):
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory

    def test_unset_registration_deadline(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.activity.registration_deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.refresh_from_db()
        self.activity.registration_deadline = None
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

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

        self.assertEqual(self.activity.status, 'open')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.start = date.today() + timedelta(days=2)
        self.activity.save()
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

    def test_change_start_notification(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.participant_factory.create(
            activity=self.activity,
        )

        self.activity.start = date.today() + timedelta(days=4)
        self.activity.save()
        self.assertTrue(
            'The activity starts on {start} and ends on {end}'.format(
                start=defaultfilters.date(self.activity.start),
                end=defaultfilters.date(self.activity.deadline)
            )
            in mail.outbox[-1].body
        )

    def test_unset_start_notification(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.participant_factory.create(
            activity=self.activity,
        )

        self.activity.start = None
        self.activity.save()
        self.assertTrue(
            'The activity starts immediately and ends on {end}'.format(
                end=defaultfilters.date(self.activity.deadline),
            )
            in mail.outbox[-1].body
        )

    def test_change_deadline_notification(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.participant_factory.create(
            activity=self.activity,
        )

        self.activity.start = date.today() + timedelta(days=40)
        self.activity.save()
        self.assertTrue(
            'The activity starts on {start} and ends on {end}'.format(
                start=defaultfilters.date(self.activity.start),
                end=defaultfilters.date(self.activity.deadline),
            )
            in mail.outbox[-1].body
        )

    def test_unset_both_notification(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.participant_factory.create(
            activity=self.activity,
        )

        self.activity.start = None
        self.activity.deadline = None
        self.activity.save()
        self.assertTrue(
            'The activity starts immediately and runs indefinitely'
            in mail.outbox[-1].body
        )

    def test_unset_start(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.activity.start = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.start = None
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
        self.assertEqual(self.activity.status, 'full')

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

        self.assertEqual(self.activity.status, 'full')

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

    def test_reschedule_contributions(self):
        self.participant_factory.create_batch(5, activity=self.activity)

        self.assertEqual(len(self.activity.durations), 5)

        tz = get_current_timezone()

        for duration in self.activity.durations:
            self.assertEqual(duration.start.astimezone(tz).date(), self.activity.start)
            self.assertEqual(duration.end.astimezone(tz).date(), self.activity.deadline)

        self.activity.start = self.activity.start + timedelta(days=1)
        self.activity.save()

        for duration in self.activity.durations:
            self.assertEqual(duration.start.astimezone(tz).date(), self.activity.start)
            self.assertEqual(duration.end.astimezone(tz).date(), self.activity.deadline)

        self.activity.deadline = self.activity.deadline + timedelta(days=1)
        self.activity.save()

        for duration in self.activity.durations:
            self.assertEqual(duration.start.astimezone(tz).date(), self.activity.start)
            self.assertEqual(duration.end.astimezone(tz).date(), self.activity.deadline)

        current_start = self.activity.start
        self.activity.start = None
        self.activity.save()

        for duration in self.activity.durations:
            self.assertEqual(duration.start.astimezone(tz).date(), current_start)
            self.assertEqual(duration.end.astimezone(tz).date(), self.activity.deadline)

        self.activity.deadline = None
        self.activity.save()

        for duration in self.activity.durations:
            self.assertEqual(duration.start.astimezone(tz).date(), current_start)
            self.assertEqual(duration.end, None)


class DateActivitySlotTriggerTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user)

        self.activity = DateActivityFactory.create(
            initiative=self.initiative,
            slots=[],
            review=False)
        self.slot = DateActivitySlotFactory.create(activity=self.activity)

        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

    def assertStatus(self, obj, status):
        obj.refresh_from_db()
        self.assertEqual(obj.status, status)

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

    def test_finish_one_slot_no_participants(self):
        self.slot.start = now() - timedelta(days=1)
        self.slot.save()
        self.assertStatus(self.slot, 'finished')
        self.assertStatus(self.activity, 'expired')

    def test_reschedule_one_slot_no_participants(self):
        self.test_finish_one_slot_no_participants()
        self.slot.start = now() + timedelta(days=1)
        self.slot.save()
        self.assertStatus(self.slot, 'open')
        self.assertStatus(self.activity, 'open')

    def test_finish_one_slot_with_participants(self):
        DateParticipantFactory.create(activity=self.activity)
        self.slot.start = now() - timedelta(days=1)
        self.slot.save()
        self.assertStatus(self.slot, 'finished')
        self.assertStatus(self.activity, 'succeeded')

    def test_reschedule_one_slot_with_participants(self):
        self.test_finish_one_slot_with_participants()
        self.slot.start = now() + timedelta(days=1)
        self.slot.save()
        self.assertStatus(self.slot, 'open')
        self.assertStatus(self.activity, 'open')

    def test_finish_multiple_slots(self):
        self.slot2 = DateActivitySlotFactory.create(activity=self.activity)
        DateParticipantFactory.create(activity=self.activity)
        self.slot.start = now() - timedelta(days=1)
        self.slot.save()
        self.assertStatus(self.slot, 'finished')
        self.assertStatus(self.activity, 'open')
        self.slot2.start = now() - timedelta(days=1)
        self.slot2.save()
        self.assertStatus(self.slot2, 'finished')
        self.assertStatus(self.activity, 'succeeded')

    def test_reschedule_open(self):
        self.test_finish_one_slot_with_participants()
        self.slot.start = now() + timedelta(days=1)
        self.slot.save()
        self.assertStatus(self.slot, 'open')

    def test_reschedule_running(self):
        self.test_finish_one_slot_with_participants()
        self.slot.start = now() - timedelta(hours=1)
        self.slot.save()
        self.assertStatus(self.slot, 'running')

    def test_reset_slot_selection(self):
        self.activity.slot_selection = 'free'
        self.activity.save()

        second_slot = DateActivitySlotFactory.create(activity=self.activity)
        third_slot = DateActivitySlotFactory.create(activity=self.activity)

        second_slot.delete()
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.slot_selection, 'free')

        third_slot.delete()
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.slot_selection, 'all')

    def test_reset_slot_selection_all(self):
        self.activity.save()

        second_slot = DateActivitySlotFactory.create(activity=self.activity)

        second_slot.delete()
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.slot_selection, 'all')

    def test_changed_single_date(self):
        eng = BlueBottleUserFactory.create(primary_language='en')
        DateParticipantFactory.create(activity=self.activity, user=eng)
        mail.outbox = []
        self.slot.start = now() + timedelta(days=10)
        self.slot.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'The details of activity "{}" have changed'.format(self.activity.title)
        )
        with TenantLanguage('en'):
            expected = '{} {} - {} ({})'.format(
                defaultfilters.date(self.slot.start),
                defaultfilters.time(self.slot.start.astimezone(get_current_timezone())),
                defaultfilters.time(self.slot.end.astimezone(get_current_timezone())),
                self.slot.start.astimezone(get_current_timezone()).strftime('%Z'),
            )

        self.assertTrue(expected in mail.outbox[0].body)

    def test_changed_multiple_dates(self):
        self.slot2 = DateActivitySlotFactory.create(activity=self.activity)
        eng = BlueBottleUserFactory.create(primary_language='en')
        DateParticipantFactory.create(activity=self.activity, user=eng)
        mail.outbox = []
        self.slot.start = now() + timedelta(days=10)

        self.slot.execute_triggers(user=self.user, send_messages=True)
        self.slot.save()

        self.assertEqual(len(mail.outbox), 1)

        self.assertEqual(
            mail.outbox[0].subject,
            'The details of activity "{}" have changed'.format(self.activity.title)
        )

        with TenantLanguage('en'):
            for slot in [self.slot, self.slot2]:
                expected = '{} {} - {} ({})'.format(
                    defaultfilters.date(slot.start),
                    defaultfilters.time(slot.start.astimezone(get_current_timezone())),
                    defaultfilters.time(slot.end.astimezone(get_current_timezone())),
                    slot.start.astimezone(get_current_timezone()).strftime('%Z'),
                )

                self.assertTrue(expected in mail.outbox[0].body)

    def test_reschedule_contributions(self):
        DateParticipantFactory.create_batch(5, activity=self.activity)

        for duration in self.slot.durations:
            self.assertEqual(duration.start, self.slot.start)
            self.assertEqual(duration.end, self.slot.start + self.slot.duration)
            self.assertEqual(duration.value, self.slot.duration)

        self.slot.start = self.slot.start + timedelta(days=1)
        self.slot.save()

        for duration in self.slot.durations:
            self.assertEqual(duration.start, self.slot.start)
            self.assertEqual(duration.end, self.slot.start + self.slot.duration)
            self.assertEqual(duration.value, self.slot.duration)

        self.slot.duration = self.slot.duration + timedelta(hours=1)
        self.slot.save()

        for duration in self.slot.durations:
            self.assertEqual(duration.start, self.slot.start)
            self.assertEqual(duration.end, self.slot.start + self.slot.duration)
            self.assertEqual(duration.value, self.slot.duration)

    def test_cancel(self):
        DateParticipantFactory.create(activity=self.activity)
        mail.outbox = []
        self.slot.title = 'Session 1'
        self.slot.states.cancel(save=True)
        self.assertEqual(self.slot.status, 'cancelled')
        self.assertEqual(
            len(mail.outbox),
            2
        )

        self.assertEqual(
            mail.outbox[1].subject,
            'A slot for your activity "{}" has been cancelled'.format(self.activity.title)
        )

        self.assertTrue(
            'Session 1' in
            mail.outbox[1].body
        )

    def test_cancel_multiple_slots(self):
        self.slot2 = DateActivitySlotFactory.create(activity=self.activity)
        self.slot.states.cancel(save=True)
        self.assertStatus(self.slot, 'cancelled')
        self.assertStatus(self.activity, 'open')

        self.slot2.states.cancel(save=True)
        self.assertStatus(self.slot2, 'cancelled')
        self.assertStatus(self.activity, 'cancelled')

    def test_cancel_multiple_slots_succeed(self):
        self.slot2 = DateActivitySlotFactory.create(activity=self.activity)

        DateParticipantFactory.create(activity=self.activity)
        self.slot.start = now() - timedelta(days=1)
        self.slot.save()
        self.assertStatus(self.slot, 'finished')
        self.assertStatus(self.activity, 'open')

        self.slot2.states.cancel(save=True)
        self.assertStatus(self.slot2, 'cancelled')
        self.assertStatus(self.activity, 'succeeded')

    def test_cancel_with_cancelled_activity(self):
        DateParticipantFactory.create(activity=self.activity)
        self.activity.states.cancel(save=True)
        mail.outbox = []
        self.slot.title = 'Session 3'
        self.slot.states.cancel(save=True)
        self.assertEqual(self.slot.status, 'cancelled')
        self.assertEqual(
            len(mail.outbox),
            1
        )

        self.assertEqual(
            mail.outbox[0].subject,
            'A slot for your activity "{}" has been cancelled'.format(self.activity.title)
        )

        self.assertTrue(
            'Session 3' in
            mail.outbox[0].body
        )


class ParticipantTriggerTestCase(object):

    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=[self.factory._meta.model.__name__.lower()]
        )

        self.user = BlueBottleUserFactory()
        self.admin_user = BlueBottleUserFactory.create(is_staff=True)
        self.initiative = InitiativeFactory.create(owner=self.user)

        self.activity = self.factory.create(
            preparation=timedelta(hours=1),
            initiative=self.initiative,
            review=False)
        self.review_activity = self.factory.create(
            preparation=timedelta(hours=4),
            initiative=self.initiative,
            review=True)

        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()
        self.review_activity.refresh_from_db()

    def test_initial_added_through_admin(self):
        mail.outbox = []
        participant = self.participant_factory.create(
            activity=self.review_activity,
            user=BlueBottleUserFactory.create(),
            as_user=self.admin_user
        )
        self.assertEqual(participant.status, 'accepted')

        self.assertEqual(len(mail.outbox), 2)

        self.assertEqual(
            mail.outbox[0].subject,
            'You have been added to the activity "{}" 🎉'.format(self.review_activity.title)
        )
        self.assertEqual(
            mail.outbox[1].subject,
            'A participant has been added to your activity "{}" 🎉'.format(self.review_activity.title)
        )
        self.assertTrue(self.review_activity.followers.filter(user=participant.user).exists())
        prep = participant.preparation_contributions.first()
        self.assertEqual(
            prep.value,
            self.review_activity.preparation
        )
        self.assertEqual(
            prep.status,
            'succeeded'
        )

    def test_initial_added_through_admin_team(self):
        self.review_activity.team_activity = Activity.TeamActivityChoices.teams
        self.review_activity.save()

        participant = self.participant_factory.create(
            activity=self.review_activity,
            user=BlueBottleUserFactory.create(),
            as_user=self.admin_user
        )
        self.assertTrue(participant.team)
        self.assertEqual(participant.team.owner, participant.user)
        self.assertEqual(participant.status, 'accepted')
        self.assertEqual(participant.team.status, 'open')

    def test_initiate_team_invite(self):
        self.activity.team_activity = Activity.TeamActivityChoices.teams
        self.activity.save()

        team_captain = self.participant_factory.create(
            activity=self.activity,
            user=BlueBottleUserFactory.create()
        )

        mail.outbox = []
        participant = self.participant_factory.create(
            activity=self.activity,
            accepted_invite=team_captain.invite,
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(participant.team, team_captain.team)
        'New team member' in [message.subject for message in mail.outbox]

    def test_initiate_team_invite_review(self):
        self.activity.team_activity = Activity.TeamActivityChoices.teams
        self.activity.review = True
        self.activity.save()

        capt = BlueBottleUserFactory.create()
        team_captain = self.participant_factory.create(
            activity=self.activity,
            user=capt,
            as_user=capt
        )

        team_captain.states.accept(save=True)

        mail.outbox = []
        participant = self.participant_factory.create(
            activity=self.activity,
            accepted_invite=team_captain.invite,
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(participant.team, team_captain.team)
        self.assertEqual(participant.status, 'accepted')

    def test_initiate_team_invite_review_after_signup(self):
        self.activity.team_activity = Activity.TeamActivityChoices.teams
        self.activity.review = True
        self.activity.save()

        capt = BlueBottleUserFactory.create()

        team_captain = self.participant_factory.create(
            activity=self.activity,
            user=capt,
            as_user=capt
        )

        mail.outbox = []
        user = BlueBottleUserFactory.create()
        participant = self.participant_factory.create(
            activity=self.activity,
            accepted_invite=team_captain.invite,
            user=user,
            as_user=user
        )

        self.assertEqual(participant.team, team_captain.team)
        team_captain.states.accept(save=True)

        self.assertEqual(team_captain.status, 'accepted')
        self.assertEqual(team_captain.team.status, 'open')
        participant.refresh_from_db()
        self.assertEqual(participant.status, 'accepted')

    def test_initial_removed_through_admin(self):
        mail.outbox = []

        participant = self.participant_factory.create(
            activity=self.review_activity,
            user=BlueBottleUserFactory.create(),
            as_user=self.admin_user
        )
        mail.outbox = []
        participant.states.remove()
        participant.execute_triggers(user=self.admin_user, send_messages=True)
        participant.save()

        self.assertEqual(participant.status, 'rejected')

        self.assertEqual(len(mail.outbox), 2)

        self.assertEqual(
            mail.outbox[0].subject,
            'You have been removed as participant for the activity "{}"'.format(self.review_activity.title)
        )
        self.assertEqual(
            mail.outbox[1].subject,
            'A participant has been removed from your activity "{}"'.format(self.review_activity.title)
        )

    def test_accept(self):
        user = BlueBottleUserFactory.create()
        participant = self.participant_factory.create(
            activity=self.review_activity,
            user=user,
            as_user=user
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
        prep = participant.preparation_contributions.first()
        self.assertEqual(
            prep.value,
            self.review_activity.preparation
        )
        self.assertEqual(
            prep.status,
            'succeeded'
        )

    def test_accept_team(self):
        self.review_activity.team_activity = Activity.TeamActivityChoices.teams
        self.review_activity.save()

        user = BlueBottleUserFactory.create()
        participant = self.participant_factory.create(
            activity=self.review_activity,
            user=user,
            as_user=user
        )

        participant.states.accept(save=True)
        self.assertTrue(participant.team)
        self.assertEqual(participant.team.owner, participant.user)

    def test_initial_review(self):
        mail.outbox = []
        user = BlueBottleUserFactory.create()
        participant = self.participant_factory.create(
            activity=self.review_activity,
            user=user,
            as_user=user
        )

        self.assertEqual(participant.status, 'new')
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[1].subject,
            'You have a new participant for your activity "{}" 🎉'.format(
                self.review_activity.title
            )
        )
        self.assertTrue(self.review_activity.followers.filter(user=participant.user).exists())
        self.assertEqual(
            participant.contributions.
            exclude(timecontribution__contribution_type='preparation').get().status,
            'new'
        )
        prep = participant.preparation_contributions.first()
        self.assertEqual(
            prep.value,
            self.review_activity.preparation
        )
        self.assertEqual(
            prep.status,
            'new'
        )

    def test_initial_team_created(self):
        self.review_activity.team_activity = Activity.TeamActivityChoices.teams
        self.review_activity.save()
        participant = self.participant_factory.create(
            activity=self.review_activity,
            user=BlueBottleUserFactory.create()
        )
        self.assertIsNotNone(participant.team)

    def test_initial_no_review(self):
        mail.outbox = []
        user = BlueBottleUserFactory.create()
        participant = self.participant_factory.create(
            activity=self.activity,
            user=user,
            as_user=user
        )

        self.assertEqual(participant.status, 'accepted')
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            'A new participant has joined your activity "{}" 🎉'.format(self.activity.title)
        )
        self.assertTrue(self.activity.followers.filter(user=participant.user).exists())
        self.assertEqual(
            self.activity.accepted_participants.get().
            contributions.exclude(timecontribution__contribution_type='preparation').get().status,
            'new'
        )
        prep = participant.preparation_contributions.first()
        self.assertEqual(
            prep.value,
            self.activity.preparation
        )
        self.assertEqual(
            prep.status,
            'succeeded'
        )

    def test_initial_no_review_team(self):
        self.activity.team_activity = Activity.TeamActivityChoices.teams
        self.activity.save()
        user = BlueBottleUserFactory.create()
        participant = self.participant_factory.create(
            activity=self.activity,
            user=user,
            as_user=user
        )

        self.assertTrue(participant.team)
        self.assertEqual(participant.team.owner, participant.user)

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
        participants = self.participant_factory.create_batch(
            self.review_activity.capacity,
            activity=self.review_activity,
            user=BlueBottleUserFactory.create(),
            as_relation='user'
        )
        self.review_activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

        for participant in participants:
            user = participant.user
            user.save()
            participant.execute_triggers(user=user, send_messages=True)
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
        participant = self.participants[0]
        participant.states.remove(save=True)

        self.assertEqual(
            participant.contributions.
            exclude(timecontribution__contribution_type='preparation').get().status,
            'failed'
        )
        prep = participant.preparation_contributions.first()
        self.assertEqual(
            prep.value,
            self.activity.preparation
        )
        self.assertEqual(
            prep.status,
            'failed'
        )

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'open')

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            'You have been removed as participant for the activity "{}"'.format(
                self.activity.title
            )
        )
        self.assertEqual(
            mail.outbox[1].subject,
            'A participant has been removed from your activity "{}"'.format(
                self.activity.title
            )
        )
        self.assertFalse(self.activity.followers.filter(user=self.participants[0].user).exists())

    def test_remove_team(self):
        self.activity.team_activity = Activity.TeamActivityChoices.teams
        self.activity.save()

        team_captain = self.participant_factory.create(
            activity=self.activity,
            user=BlueBottleUserFactory.create()
        )

        participant = self.participant_factory.create(
            activity=self.activity,
            accepted_invite=team_captain.invite,
            user=BlueBottleUserFactory.create()
        )

        mail.outbox = []

        participant.states.remove(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(
            participant.contributions.
            exclude(timecontribution__contribution_type='preparation').get().status,
            'failed'
        )

        subjects = [mail.subject for mail in mail.outbox]
        self.assertTrue(
            f"Your team participation in ‘{self.activity.title}’ has been cancelled" in subjects
        )

        self.assertTrue(
            f"Team member removed for ‘{self.activity.title}’" in subjects
        )

    def test_reject(self):
        users = BlueBottleUserFactory.create_batch(self.activity.capacity)
        self.participants = []
        for user in users:
            participant = self.participant_factory.build(
                user=user,
                activity=self.review_activity,
            )
            participant.execute_triggers(user=user)
            participant.save()

            self.participants.append(
                participant
            )

        mail.outbox = []
        participant = self.participants[0]
        participant.states.reject(save=True)

        self.assertEqual(
            participant.contributions.
            exclude(timecontribution__contribution_type='preparation').get().status,
            'failed'
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'You have not been selected for the activity "{}"'.format(
                self.review_activity.title
            )
        )
        self.assertFalse(self.review_activity.followers.filter(user=participant.user).exists())

    def test_reaccept(self):
        self.test_remove()

        self.participants[0].states.accept(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'full')

        self.assertEqual(
            self.participants[0].contributions.
            exclude(timecontribution__contribution_type='preparation').get().status,
            'new'
        )
        self.assertTrue(self.activity.followers.filter(user=self.participants[0].user).exists())

    def test_withdraw(self):
        self.participants = self.participant_factory.create_batch(
            self.activity.capacity,
            activity=self.activity,
            user=BlueBottleUserFactory.create()
        )
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')
        mail.outbox = []

        self.participants[0].states.withdraw(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'open')

        self.assertEqual(
            self.participants[0].contributions.
            exclude(timecontribution__contribution_type='preparation').get().status,
            'failed'
        )

        self.assertFalse(self.activity.followers.filter(user=self.participants[0].user).exists())

        subjects = [mail.subject for mail in mail.outbox]
        self.assertTrue(
            f'You have withdrawn from the activity "{self.activity.title}"' in subjects
        )
        self.assertTrue(
            f'A participant has withdrawn from your activity "{self.activity.title}"' in subjects
        )

    def test_withdraw_team(self):
        self.activity.team_activity = Activity.TeamActivityChoices.teams
        self.activity.save()

        team_captain = self.participant_factory.create(
            activity=self.activity,
            user=BlueBottleUserFactory.create()
        )

        mail.outbox = []
        participant = self.participant_factory.create(
            activity=self.activity,
            accepted_invite=team_captain.invite,
            user=BlueBottleUserFactory.create()
        )
        participant.states.withdraw(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(
            participant.contributions.
            exclude(timecontribution__contribution_type='preparation').get().status,
            'failed'
        )

        subjects = [mail.subject for mail in mail.outbox]
        self.assertTrue(
            f'You have withdrawn from the activity "{self.activity.title}"' in subjects
        )
        self.assertTrue(
            f'A participant has withdrawn from your activity "{self.activity.title}"' in subjects
        )

        self.assertTrue(
            f"Withdrawal for '{self.activity.title}'" in subjects
        )

    def test_reapply(self):
        self.test_withdraw()

        self.participants[0].states.reapply(save=True)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')
        self.assertEqual(
            self.participants[0].contributions.
            exclude(timecontribution__contribution_type='preparation').get().status,
            'new'
        )
        self.assertTrue(self.activity.followers.filter(user=self.participants[0].user).exists())

    def test_reapply_cancelled_team(self):
        self.activity.team_activity = Activity.TeamActivityChoices.teams
        self.test_withdraw()
        self.participants[0].team.states.cancel(save=True)

        self.assertEqual(
            self.participants[0].contributions.
            exclude(timecontribution__contribution_type='preparation').get().status,
            'failed'
        )

        self.participants[0].states.reapply(save=True)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')
        self.assertEqual(
            self.participants[0].contributions.
            exclude(timecontribution__contribution_type='preparation').get().status,
            'failed'
        )
        self.assertTrue(self.activity.followers.filter(user=self.participants[0].user).exists())


class DateParticipantTriggerTestCase(ParticipantTriggerTestCase, BluebottleTestCase):
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory

    def test_type(self):
        self.participants = self.participant_factory.create_batch(
            self.activity.capacity, activity=self.review_activity
        )
        self.assertEqual(
            self.participants[0].contributions.
            exclude(timecontribution__contribution_type='preparation').get().contribution_type,
            'date'
        )


@mock.patch.object(
    ParticipantJoinedNotification, 'delay', 2
)
@mock.patch.object(
    ParticipantAppliedNotification, 'delay', 1
)
@mock.patch.object(
    ParticipantChangedNotification, 'delay', 2
)
class DateParticipantTriggerCeleryTestCase(CeleryTestCase):
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory

    factories = CeleryTestCase.factories + [
        DateParticipantFactory, DateActivityFactory, InitiativeFactory
    ]

    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=[self.factory._meta.model.__name__.lower()]
        )

        self.user = BlueBottleUserFactory()
        self.admin_user = BlueBottleUserFactory(is_staff=True)
        self.initiative = InitiativeFactory(owner=self.user)

        self.activity = self.factory.create(
            preparation=timedelta(hours=1),
            initiative=self.initiative,
            slot_selection='free',
            review=False
        )
        self.slots = DateActivitySlotFactory.create_batch(3, activity=self.activity)

        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()
        self.participant = None

    def test_join_all(self):
        mail.outbox = []
        self.activity.slot_selection = 'all'
        self.activity.save()

        user = BlueBottleUserFactory.create()
        self.participant_factory.create(
            activity=self.activity,
            user=user,
            as_user=user
        )

        time.sleep(4)

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            f'A new participant has joined your activity "{self.activity.title}" 🎉'
        )
        self.assertEqual(
            mail.outbox[1].subject,
            f'You have joined the activity "{self.activity.title}"'
        )
        for slot in self.slots:
            expected = '{} {} - {} ({})'.format(
                defaultfilters.date(slot.start),
                defaultfilters.time(slot.start.astimezone(get_current_timezone())),
                defaultfilters.time(slot.end.astimezone(get_current_timezone())),
                slot.start.astimezone(get_current_timezone()).strftime('%Z'),
            )

            self.assertTrue(expected in mail.outbox[1].body)

    def test_join_free(self):
        mail.outbox = []

        user = BlueBottleUserFactory.create()
        participant = self.participant_factory.create(
            activity=self.activity,
            user=user,
            as_user=user
        )

        self.slot_participants = [
            SlotParticipantFactory.create(slot=slot, participant=participant)
            for slot in self.slots
        ]

        time.sleep(3)

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            f'A new participant has joined your activity "{self.activity.title}" 🎉'
        )
        self.assertEqual(
            mail.outbox[1].subject,
            f'You have joined the activity "{self.activity.title}"'
        )

        for slot in self.slots:
            self.assertTrue(slot.title in mail.outbox[1].body)

    def test_join_free_review(self):
        self.activity.review = True
        self.activity.save()

        mail.outbox = []

        user = BlueBottleUserFactory.create()
        participant = self.participant_factory.create(
            activity=self.activity,
            user=user,
            as_user=user
        )

        self.slot_participants = [
            SlotParticipantFactory.create(slot=slot, participant=participant)
            for slot in self.slots
        ]

        time.sleep(3)

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            f'You have a new participant for your activity "{self.activity.title}" 🎉'
        )
        self.assertEqual(
            mail.outbox[1].subject,
            f'You have applied to the activity "{self.activity.title}"'
        )

    def test_change_free(self):
        self.test_join_free()

        time.sleep(3)
        mail.outbox = []

        for slot_participant in self.slot_participants[:-1]:
            slot_participant.states.withdraw(save=True)

        time.sleep(3)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            f'You have changed your application on the activity "{self.activity.title}"'
        )

        for slot in self.slots[:-1]:
            self.assertTrue(slot.title not in mail.outbox[0].body)

        self.assertTrue(self.slots[2].title in mail.outbox[0].body)

    def test_withdraw_free(self):
        self.test_join_free()

        time.sleep(3)
        mail.outbox = []

        for slot_participant in self.slot_participants:
            slot_participant.states.withdraw(save=True)

        time.sleep(3)

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            f'A participant has withdrawn from your activity "{self.activity.title}"'
        )

        self.assertEqual(
            mail.outbox[1].subject,
            f'You have withdrawn from the activity "{self.activity.title}"'
        )


class PeriodParticipantTriggerTestCase(ParticipantTriggerTestCase, TriggerTestCase):
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory

    def test_initial_added_with_team_through_admin(self):
        captain = BlueBottleUserFactory.create(email='captain@example.com')
        team = TeamFactory.create(
            activity=self.activity,
            owner=captain
        )
        PeriodParticipantFactory.create(
            user=captain,
            activity=self.activity,
            team=team
        )

        mail.outbox = []
        self.activity.team_activity = 'teams'
        self.activity.save()
        participant = self.participant_factory.build(
            activity=self.activity,
            user=BlueBottleUserFactory.create(),
            team=team
        )
        participant.execute_triggers(user=self.admin_user, send_messages=True)
        participant.save()

        self.assertEqual(len(mail.outbox), 2)

        self.assertEqual(
            mail.outbox[1].subject,
            'A participant has been added to your activity "{}" 🎉'.format(self.activity.title)
        )

        self.assertEqual(
            mail.outbox[0].subject,
            'You have been added to a team for "{}" 🎉'.format(self.activity.title)
        )

    def test_join(self):
        mail.outbox = []
        participant = self.participant_factory.create(
            activity=self.activity,
            user=BlueBottleUserFactory.create(),
            as_relation='user'
        )
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            f'A new participant has joined your activity "{self.activity.title}" 🎉'
        )
        self.assertEqual(
            mail.outbox[1].subject,
            f'You have joined the activity "{self.activity.title}"'
        )
        prep = participant.preparation_contributions.first()
        self.assertEqual(
            prep.value,
            self.activity.preparation
        )
        self.assertEqual(
            prep.status,
            'succeeded'
        )

    def test_team_join(self):
        self.activity.team_activity = Activity.TeamActivityChoices.teams
        self.activity.save()
        mail.outbox = []
        user = BlueBottleUserFactory.create()
        participant = self.participant_factory.create(
            activity=self.activity,
            user=user,
            as_user=user
        )
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            f'A new team has joined "{self.activity.title}"'
        )
        self.assertEqual(
            mail.outbox[1].subject,
            f'You have registered your team for "{self.activity.title}"'
        )
        prep = participant.preparation_contributions.first()
        self.assertEqual(
            prep.value,
            self.activity.preparation
        )
        self.assertEqual(
            prep.status,
            'succeeded'
        )

    def test_apply(self):
        mail.outbox = []
        participant = self.participant_factory.create(
            activity=self.review_activity,
            user=BlueBottleUserFactory.create(),
            as_relation='user'
        )
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[1].subject,
            f'You have a new participant for your activity "{self.review_activity.title}" 🎉'
        )
        self.assertEqual(
            mail.outbox[0].subject,
            f'You have applied to the activity "{self.review_activity.title}"'
        )
        prep = participant.preparation_contributions.first()
        self.assertEqual(
            prep.value,
            self.review_activity.preparation
        )
        self.assertEqual(
            prep.status,
            'new'
        )

    def test_team_apply(self):
        self.review_activity.team_activity = Activity.TeamActivityChoices.teams
        self.review_activity.save()
        mail.outbox = []
        participant = self.participant_factory.create(
            activity=self.review_activity,
            user=BlueBottleUserFactory.create(),
            as_relation='user'
        )
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[1].subject,
            f'You have registered your team for "{self.review_activity.title}"'
        )
        self.assertEqual(
            mail.outbox[0].subject,
            f'A new team has applied to "{self.review_activity.title}"'
        )
        prep = participant.preparation_contributions.first()
        self.assertEqual(
            prep.value,
            self.review_activity.preparation
        )
        self.assertEqual(
            prep.status,
            'new'
        )

    def test_team_accept(self):
        self.review_activity.team_activity = Activity.TeamActivityChoices.teams
        self.review_activity.save()

        participant = self.participant_factory.create(
            activity=self.review_activity,
            user=BlueBottleUserFactory.create(),
            as_relation='user'
        )

        mail.outbox = []
        participant.states.accept(save=True)
        self.assertEqual(participant.status, 'accepted')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'Your team has been accepted for "{}"'.format(
                self.review_activity.title
            )
        )
        prep = participant.preparation_contributions.first()
        self.assertEqual(
            prep.value,
            self.review_activity.preparation
        )
        self.assertEqual(
            prep.status,
            'succeeded'
        )

    def test_no_review_succeed(self):
        self.activity.deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'expired')

        participant = self.participant_factory.create(activity=self.activity)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'succeeded')

        self.assertEqual(
            participant.contributions.
            exclude(timecontribution__contribution_type='preparation').get().status,
            'succeeded'
        )

        self.assertEqual(
            participant.contributions.
            exclude(timecontribution__contribution_type='preparation').get().contribution_type,
            'period'
        )

    def test_stop(self):
        participant = self.participant_factory.create(activity=self.activity)
        self.activity.start = date.today() - timedelta(days=1)
        self.activity.save()

        participant.states.stop(save=True)

        self.assertEqual(
            mail.outbox[-1].subject,
            'Your contribution to the activity "{}" is successful 🎉'.format(self.activity.title)
        )

    def test_join_participant(self):
        user = BlueBottleUserFactory.create()
        self.model = self.participant_factory.build(
            activity=self.activity,
            user=user
        )
        with self.execute(user=user):
            self.assertNotificationEffect(NewParticipantNotification)
            self.assertNotificationEffect(ParticipantJoinedNotification)

    def test_add_participant(self):
        user = BlueBottleUserFactory.create()
        self.model = self.participant_factory.build(
            activity=self.activity,
            user=user
        )
        staff = BlueBottleUserFactory.create(is_staff=True)
        with self.execute(user=staff):
            self.assertNotificationEffect(ParticipantAddedOwnerNotification)
            self.assertNotificationEffect(ParticipantAddedNotification)

    def test_start_team_participant(self):
        self.activity.team_activity = 'teams'
        self.activity.save()
        user = BlueBottleUserFactory.create()
        self.model = self.participant_factory.build(
            activity=self.activity,
            user=user
        )
        with self.execute(user=user):
            self.assertNoNotificationEffect(NewParticipantNotification)
            self.assertNotificationEffect(TeamParticipantJoinedNotification)

    def test_join_team_participant(self):
        self.activity.team_activity = 'teams'
        self.activity.save()
        user = BlueBottleUserFactory.create()
        captain = BlueBottleUserFactory.create()
        team = TeamFactory.create(
            owner=captain,
            activity=self.activity
        )
        self.model = self.participant_factory.build(
            team=team,
            activity=self.activity,
            user=user
        )
        with self.execute(user=user):
            self.assertNoNotificationEffect(NewParticipantNotification)
            self.assertNotificationEffect(TeamParticipantJoinedNotification)
            self.assertNotificationEffect(ParticipantJoinedNotification)

    def test_remove_participant(self):
        self.model = self.participant_factory.create(
            activity=self.activity,
            status='accepted'
        )
        self.model.states.remove()
        with self.execute():
            self.assertNotificationEffect(ParticipantRemovedNotification)
            self.assertNotificationEffect(ParticipantRemovedOwnerNotification)

    def test_remove_team_participant(self):
        self.activity.team_activity = 'teams'
        self.activity.save()
        team = TeamFactory.create(
            owner=BlueBottleUserFactory.create(),
            activity=self.activity
        )
        self.model = self.participant_factory.create(
            activity=self.activity,
            team=team,
            status='accepted'
        )
        self.model.states.remove()
        with self.execute():
            self.assertNotificationEffect(ParticipantRemovedNotification)
            self.assertNotificationEffect(TeamMemberRemovedMessage)
            self.assertNoNotificationEffect(ParticipantRemovedOwnerNotification)

    def test_remove_team_participant_by_captain(self):
        self.activity.team_activity = 'teams'
        self.activity.save()
        captain = BlueBottleUserFactory.create()
        team = TeamFactory.create(
            owner=captain,
            activity=self.activity
        )
        self.model = self.participant_factory.create(
            activity=self.activity,
            team=team,
            status='accepted'
        )
        self.model.states.remove()
        with self.execute(user=captain):
            self.assertNotificationEffect(ParticipantRemovedNotification)
            self.assertNoNotificationEffect(TeamMemberRemovedMessage)
            self.assertNoNotificationEffect(ParticipantRemovedOwnerNotification)


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
            capacity=None,
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

    def test_withdraw_from_all_slots(self):
        slot_participant1 = SlotParticipantFactory.create(slot=self.slot1, participant=self.participant)
        slot_participant2 = SlotParticipantFactory.create(slot=self.slot2, participant=self.participant)

        slot_participant1.states.withdraw(save=True)
        self.assertStatus(self.participant, 'accepted')
        self.assertStatus(slot_participant1, 'withdrawn')

        slot_participant2.states.withdraw(save=True)
        self.assertStatus(self.participant, 'withdrawn')
        self.assertStatus(slot_participant2, 'withdrawn')

        slot_participant1.states.reapply(save=True)

        self.assertStatus(self.participant, 'accepted')
        self.assertStatus(slot_participant1, 'registered')

        slot_participant2.states.reapply(save=True)
        self.assertStatus(self.participant, 'accepted')
        self.assertStatus(slot_participant2, 'registered')

    def test_remove_from_all_slots(self):
        slot_participant1 = SlotParticipantFactory.create(slot=self.slot1, participant=self.participant)
        slot_participant2 = SlotParticipantFactory.create(slot=self.slot2, participant=self.participant)

        slot_participant1.states.remove(save=True)
        self.assertStatus(self.participant, 'accepted')
        self.assertStatus(slot_participant1, 'removed')

        slot_participant2.states.remove(save=True)
        self.assertStatus(self.participant, 'rejected')
        self.assertStatus(slot_participant2, 'removed')

        slot_participant1.states.accept(save=True)

        self.assertStatus(self.participant, 'accepted')
        self.assertStatus(slot_participant1, 'registered')

        slot_participant2.states.accept(save=True)
        self.assertStatus(self.participant, 'accepted')
        self.assertStatus(slot_participant2, 'registered')

    def test_fill_slot(self):
        SlotParticipantFactory.create(slot=self.slot1, participant=self.participant)
        self.assertStatus(self.slot1, 'open')
        participant2 = DateParticipantFactory.create(activity=self.activity)
        SlotParticipantFactory.create(slot=self.slot1, participant=participant2)
        self.assertStatus(self.slot1, 'full')
        self.assertStatus(self.activity, 'open')
        SlotParticipantFactory.create(slot=self.slot2, participant=self.participant)
        self.assertStatus(self.slot2, 'full')
        self.assertStatus(self.activity, 'full')

    def test_fill_slot_ignores_activity_capacity(self):
        self.activity.capacity = 1
        self.activity.save()
        SlotParticipantFactory.create(slot=self.slot1, participant=self.participant)
        self.assertStatus(self.slot1, 'open')
        self.assertStatus(self.activity, 'open')

    def test_unfill_slot(self):
        self.slot_part = SlotParticipantFactory.create(slot=self.slot2, participant=self.participant)
        self.assertStatus(self.slot2, 'full')
        self.assertStatus(self.activity, 'open')
        SlotParticipantFactory.create(slot=self.slot1, participant=self.participant)
        participant2 = DateParticipantFactory.create(activity=self.activity)
        SlotParticipantFactory.create(slot=self.slot1, participant=participant2)
        self.assertStatus(self.slot1, 'full')
        self.assertStatus(self.activity, 'full')
        self.slot_part.states.withdraw(save=True)
        self.assertStatus(self.slot2, 'open')
        self.assertStatus(self.activity, 'open')

    def test_fill_new_slot(self):
        self.slot_part = SlotParticipantFactory.create(slot=self.slot2, participant=self.participant)
        self.assertStatus(self.slot2, 'full')
        self.assertStatus(self.activity, 'open')
        SlotParticipantFactory.create(slot=self.slot1, participant=self.participant)
        participant2 = DateParticipantFactory.create(activity=self.activity)
        SlotParticipantFactory.create(slot=self.slot1, participant=participant2)
        self.assertStatus(self.slot1, 'full')
        self.assertStatus(self.activity, 'full')

        new_slot = DateActivitySlotFactory.create(
            activity=self.activity,
            capacity=1
        )

        self.assertStatus(self.activity, 'open')

        new_slot.delete()

        self.assertStatus(self.activity, 'full')

    def test_expire_new_slot(self):
        self.participant.delete()

        self.slot1.start = now() - timedelta(days=1)
        self.slot1.save()
        self.assertStatus(self.slot1, 'finished')
        self.assertStatus(self.activity, 'open')

        self.slot2.start = now() - timedelta(days=1)
        self.slot2.save()
        self.assertStatus(self.slot2, 'finished')
        self.assertStatus(self.activity, 'expired')

        new_slot = DateActivitySlotFactory.create(
            activity=self.activity,
            capacity=1
        )

        self.assertStatus(self.activity, 'open')

        new_slot.delete()

        self.assertStatus(self.activity, 'expired')

    def test_succeed_new_slot(self):
        SlotParticipantFactory.create(slot=self.slot1, participant=self.participant)
        self.slot1.start = now() - timedelta(days=1)
        self.slot1.save()
        self.assertStatus(self.slot1, 'finished')
        self.assertStatus(self.activity, 'open')

        SlotParticipantFactory.create(slot=self.slot2, participant=self.participant)
        self.slot2.start = now() - timedelta(days=1)
        self.slot2.save()
        self.assertStatus(self.slot2, 'finished')
        self.assertStatus(self.activity, 'succeeded')

        new_slot = DateActivitySlotFactory.create(
            activity=self.activity,
            capacity=1
        )

        self.assertStatus(self.activity, 'open')

        new_slot.delete()

        self.assertStatus(self.activity, 'succeeded')

    def test_refill_slot(self):
        self.test_unfill_slot()
        self.slot_part.states.reapply(save=True)
        self.assertStatus(self.slot2, 'full')

    def test_unfill_slot_remove(self):
        self.slot_part = SlotParticipantFactory.create(slot=self.slot2, participant=self.participant)
        self.assertStatus(self.slot2, 'full')
        self.slot_part.states.remove(save=True)
        self.assertStatus(self.slot2, 'open')

    def test_refill_slot_remove(self):
        self.test_unfill_slot_remove()
        self.slot_part.states.accept(save=True)
        self.assertStatus(self.slot2, 'full')


class TeamSlotTriggerTestCase(TriggerTestCase):

    def setUp(self):
        super().setUp()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user)

        self.activity = PeriodActivityFactory.create(
            initiative=self.initiative,
            team_activity='teams',
            status='approved',
            review=False)
        self.participant = PeriodParticipantFactory.create(
            user=self.user,
            activity=self.activity
        )

    def assertStatus(self, obj, status):
        obj.refresh_from_db()
        self.assertEqual(obj.status, status)

    def test_set_date(self):
        self.assertTrue(self.participant.team)
        start = now() + timedelta(days=4)
        self.model = TeamSlotFactory.build(
            team=self.participant.team,
            activity=self.activity,
            start=start,
            duration=timedelta(hours=2)
        )
        with self.execute():
            self.assertNotificationEffect(TeamSlotChangedNotification)
        self.assertEqual(self.model.status, 'open')

        self.model.start = now() + timedelta(days=1)
        with self.execute():
            self.assertNotificationEffect(TeamSlotChangedNotification)
        self.assertEqual(self.model.status, 'open')
