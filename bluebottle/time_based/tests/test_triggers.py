from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.core import mail
from django.template import defaultfilters
from django.utils.timezone import get_current_timezone, now, make_aware
from tenant_extras.utils import TenantLanguage

from bluebottle.activities.messages.participant import InactiveParticipantAddedNotification
from bluebottle.activities.models import Organizer
from bluebottle.initiatives.tests.factories import (
    InitiativeFactory,
    InitiativePlatformSettingsFactory,
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, TriggerTestCase
from bluebottle.time_based.effects.effects import (
    CreateNextSlotEffect,
    CreatePeriodicParticipantsEffect,
)
from bluebottle.time_based.messages import (
    ParticipantAddedNotification, ManagerParticipantAddedOwnerNotification,
)
from bluebottle.time_based.notifications.participants import UserScheduledNotification
from bluebottle.time_based.notifications.registrations import ManagerRegistrationCreatedNotification, \
    ManagerRegistrationCreatedReviewNotification, \
    UserRegistrationAcceptedNotification, UserRegistrationRejectedNotification, UserRegistrationStoppedNotification, \
    UserRegistrationRestartedNotification, PeriodicUserAppliedNotification, PeriodicUserJoinedNotification, \
    ScheduleUserJoinedNotification
from bluebottle.time_based.states.participants import PeriodicParticipantStateMachine
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DateParticipantFactory,
    PeriodicActivityFactory,
    PeriodicRegistrationFactory,
    PeriodicSlotFactory,
    SlotParticipantFactory, ScheduleRegistrationFactory,
    ScheduleActivityFactory, ScheduleSlotFactory, )


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
        self.initiative.states.approve(save=True)
        self.activity.states.publish(save=True)
        mail.outbox = []

        self.activity.states.reject(save=True)
        organizer = self.activity.contributors.instance_of(Organizer).get()
        self.assertEqual(organizer.status, 'failed')
        self.assertEqual(
            mail.outbox[0].subject,
            'Your activity "{}" has been rejected'.format(self.activity.title)
        )

    def test_submit_initiative(self):
        self.initiative.states.submit(save=True)
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'submitted')

    def test_publish_initiative_already_approved(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        activity = self.factory.create(initiative=self.initiative)
        activity.states.publish(save=True)

        self.assertEqual(activity.status, 'open')

    def test_submit_initiative_not_approved(self):
        self.initiative.states.submit(save=True)

        activity = self.factory.create(initiative=self.initiative)
        if self.activity.states.submit:
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

        self.assertEqual(self.activity.status, "open")

    def change_registration_deadline(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.activity.registration_deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, "full")

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.registration_deadline = date.today() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, "open")

    def test_change_preparation_time(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.participant_factory.create_batch(
            3, activity=self.activity, status="accepted"
        )

        self.activity.preparation = timedelta(hours=2)
        self.activity.save()

        for participant in self.activity.participants.all():
            preparation_contributions = participant.contributions.filter(
                timecontribution__contribution_type="preparation"
            )

            self.assertEqual(len(preparation_contributions), 1)
            self.assertEqual(preparation_contributions.get().value, timedelta(hours=2))

        self.activity.preparation = None
        self.activity.save()

        for participant in self.activity.participants.all():
            preparation_contributions = participant.contributions.filter(
                timecontribution__contribution_type="preparation"
            )

            self.assertEqual(len(preparation_contributions), 0)


class DateActivityTriggerTestCase(TimeBasedActivityTriggerTestCase, BluebottleTestCase):
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory

    def test_unset_registration_deadline(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.activity.registration_deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, "full")

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.refresh_from_db()
        self.activity.registration_deadline = None
        self.activity.save()

        self.assertEqual(self.activity.status, "open")


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

        self.assertEqual(self.slot.status, "running")

    def test_finish_one_slot_no_participants(self):
        self.slot.start = now() - timedelta(days=1)
        self.slot.save()
        self.assertStatus(self.slot, "finished")
        self.assertStatus(self.activity, "expired")

    def test_reschedule_one_slot_no_participants(self):
        self.test_finish_one_slot_no_participants()
        self.slot.start = now() + timedelta(days=1)
        self.slot.save()
        self.assertStatus(self.slot, "open")
        self.assertStatus(self.activity, "open")

    def test_fill_free(self):
        self.slot2 = DateActivitySlotFactory.create(activity=self.activity, capacity=3)

        self.slot.capacity = 2
        self.slot.save()

        first = DateParticipantFactory.create(activity=self.activity)
        second = DateParticipantFactory.create(activity=self.activity)
        third = DateParticipantFactory.create(activity=self.activity)

        SlotParticipantFactory.create(participant=first, slot=self.slot)
        SlotParticipantFactory.create(participant=second, slot=self.slot)

        SlotParticipantFactory.create(participant=first, slot=self.slot2)
        SlotParticipantFactory.create(participant=second, slot=self.slot2)
        SlotParticipantFactory.create(participant=third, slot=self.slot2)

        self.assertStatus(self.slot, "full")
        self.assertStatus(self.slot2, "full")
        self.assertStatus(self.activity, "full")

    def test_fill_cancel_slot(self):
        self.slot2 = DateActivitySlotFactory.create(activity=self.activity, capacity=3)

        self.slot.capacity = 2
        self.slot.save()

        first = DateParticipantFactory.create(activity=self.activity)
        second = DateParticipantFactory.create(activity=self.activity)

        SlotParticipantFactory.create(participant=first, slot=self.slot)
        SlotParticipantFactory.create(participant=second, slot=self.slot)

        self.slot2.states.cancel(save=True)

        self.assertStatus(self.slot, "full")
        self.assertStatus(self.activity, "full")

    def test_full_create_new_slot(self):
        self.test_fill_free()
        DateActivitySlotFactory.create(activity=self.activity, capacity=3)

        self.assertStatus(self.activity, "open")

    def test_finish_one_slot_with_participants(self):
        DateParticipantFactory.create(activity=self.activity)
        self.slot.start = now() - timedelta(days=1)
        self.slot.save()
        self.assertStatus(self.slot, "finished")
        self.assertStatus(self.activity, "succeeded")

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
        self.assertStatus(self.slot, "finished")
        self.assertStatus(self.activity, "open")
        self.slot2.start = now() - timedelta(days=1)
        self.slot2.save()
        self.assertStatus(self.slot2, "finished")
        self.assertStatus(self.activity, "succeeded")

    def test_reschedule_open(self):
        self.test_finish_one_slot_with_participants()
        self.slot.start = now() + timedelta(days=1)
        self.slot.save()
        self.assertStatus(self.slot, "open")

    def test_reschedule_running(self):
        self.test_finish_one_slot_with_participants()
        self.slot.start = now() - timedelta(hours=1)
        self.slot.save()
        self.assertStatus(self.slot, "running")

    def test_changed_single_date(self):
        eng = BlueBottleUserFactory.create(primary_language="en")
        participant = DateParticipantFactory.create(activity=self.activity, user=eng)
        SlotParticipantFactory.create(
            participant=participant, slot=self.activity.slots.get()
        )

        mail.outbox = []
        self.slot.start = now() + timedelta(days=10)
        self.slot.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'The details of activity "{}" have changed'.format(self.activity.title),
        )
        with TenantLanguage("en"):
            expected_date = defaultfilters.date(self.slot.start)
            expected_time = "{} to {} ({})".format(
                defaultfilters.time(self.slot.start.astimezone(get_current_timezone())),
                defaultfilters.time(self.slot.end.astimezone(get_current_timezone())),
                self.slot.start.astimezone(get_current_timezone()).strftime("%Z"),
            )

        self.assertTrue(expected_date in mail.outbox[0].body)
        self.assertTrue(expected_time in mail.outbox[0].body)

    def test_changed_multiple_dates(self):
        eng = BlueBottleUserFactory.create(primary_language="en")
        participant = DateParticipantFactory.create(activity=self.activity, user=eng)
        SlotParticipantFactory.create(participant=participant, slot=self.slot)

        slot2 = DateActivitySlotFactory.create(activity=self.activity)
        other_participant = DateParticipantFactory.create(activity=self.activity)
        SlotParticipantFactory.create(slot=slot2, participant=other_participant)

        mail.outbox = []
        self.slot.start = now() + timedelta(days=10)

        self.slot.execute_triggers(user=self.user, send_messages=True)
        self.slot.save()

        self.assertEqual(len(mail.outbox), 1)

        self.assertEqual(
            mail.outbox[0].subject,
            'The details of activity "{}" have changed'.format(self.activity.title),
        )

        self.assertEqual(mail.outbox[0].to[0], participant.user.email)

        with TenantLanguage("en"):
            expected_date = defaultfilters.date(self.slot.start)
            expected_time = "{} to {} ({})".format(
                defaultfilters.time(self.slot.start.astimezone(get_current_timezone())),
                defaultfilters.time(self.slot.end.astimezone(get_current_timezone())),
                self.slot.start.astimezone(get_current_timezone()).strftime("%Z"),
            )

        self.assertTrue(expected_date in mail.outbox[0].body)
        self.assertTrue(expected_time in mail.outbox[0].body)

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
        participant = DateParticipantFactory.create(activity=self.activity)
        SlotParticipantFactory.create(
            participant=participant, slot=self.activity.slots.get()
        )

        mail.outbox = []
        self.slot.title = "Session 1"
        self.slot.states.cancel(save=True)
        self.assertEqual(self.slot.status, "cancelled")
        self.assertEqual(len(mail.outbox), 3)

        self.assertEqual(
            mail.outbox[1].subject,
            'A slot for your activity "{}" has been cancelled'.format(
                self.activity.title
            ),
        )

        self.assertTrue("Session 1" in mail.outbox[1].body)

    def test_cancel_multiple_slots(self):
        self.slot2 = DateActivitySlotFactory.create(activity=self.activity)
        self.slot.states.cancel(save=True)
        self.assertStatus(self.slot, "cancelled")
        self.assertStatus(self.activity, "open")

        self.slot2.states.cancel(save=True)
        self.assertStatus(self.slot2, "cancelled")
        self.assertStatus(self.activity, "cancelled")

    def test_cancel_multiple_slots_succeed(self):
        self.slot2 = DateActivitySlotFactory.create(activity=self.activity)

        DateParticipantFactory.create(activity=self.activity)
        self.slot.start = now() - timedelta(days=1)
        self.slot.save()
        self.assertStatus(self.slot, "finished")
        self.assertStatus(self.activity, "open")

        self.slot2.states.cancel(save=True)
        self.assertStatus(self.slot2, "cancelled")
        self.assertStatus(self.activity, "succeeded")

    def test_cancel_with_cancelled_activity(self):
        participant = DateParticipantFactory.create(activity=self.activity)
        SlotParticipantFactory.create(
            participant=participant, slot=self.activity.slots.get()
        )

        self.activity.states.cancel(save=True)
        mail.outbox = []
        self.slot.title = "Session 3"
        self.slot.states.cancel(save=True)
        self.assertEqual(self.slot.status, "cancelled")
        self.assertEqual(len(mail.outbox), 2)

        self.assertEqual(
            mail.outbox[0].subject,
            'A slot for your activity "{}" has been cancelled'.format(
                self.activity.title
            ),
        )

        self.assertTrue("Session 3" in mail.outbox[0].body)

    def test_lock_on_start(self):
        self.slot2 = DateActivitySlotFactory.create(activity=self.activity, capacity=3)

        self.slot.capacity = 2
        self.slot.save()

        first = DateParticipantFactory.create(activity=self.activity)
        second = DateParticipantFactory.create(activity=self.activity)
        third = DateParticipantFactory.create(activity=self.activity)

        SlotParticipantFactory.create(participant=first, slot=self.slot)

        SlotParticipantFactory.create(participant=first, slot=self.slot2)
        SlotParticipantFactory.create(participant=second, slot=self.slot2)
        SlotParticipantFactory.create(participant=third, slot=self.slot2)

        self.slot.states.start(save=True)
        self.assertStatus(self.slot, "running")
        self.assertStatus(self.slot2, "full")
        self.assertStatus(self.activity, "full")
        self.slot.start = now() - timedelta(days=1)
        self.slot.save()
        self.assertStatus(self.slot, "finished")
        self.assertStatus(self.slot2, "full")
        self.assertStatus(self.activity, "full")

    def test_start_single_slot(self):
        self.slot.capacity = 2
        self.slot.save()

        first = DateParticipantFactory.create(activity=self.activity)
        SlotParticipantFactory.create(participant=first, slot=self.slot)

        self.slot.states.start(save=True)
        self.assertStatus(self.slot, "running")
        self.assertStatus(self.activity, "full")
        self.slot.start = now() - timedelta(days=1)
        self.slot.save()
        self.assertStatus(self.slot, "finished")
        self.assertStatus(self.activity, "succeeded")

    def test_cancel_and_restore(self):
        self.slot2 = DateActivitySlotFactory.create(activity=self.activity, capacity=3)

        self.slot.capacity = 2
        self.slot.save()

        first = DateParticipantFactory.create(activity=self.activity)
        second = DateParticipantFactory.create(activity=self.activity)
        third = DateParticipantFactory.create(activity=self.activity)

        SlotParticipantFactory.create(participant=first, slot=self.slot)

        SlotParticipantFactory.create(participant=first, slot=self.slot2)
        SlotParticipantFactory.create(participant=second, slot=self.slot2)
        SlotParticipantFactory.create(participant=third, slot=self.slot2)

        self.assertStatus(self.slot2, "full")
        self.assertStatus(self.slot, "open")
        self.assertStatus(self.activity, "open")

        self.slot.states.cancel(save=True)
        self.assertStatus(self.slot2, "full")
        self.assertStatus(self.slot, "cancelled")
        self.assertStatus(self.activity, "full")

        self.slot.states.reopen(save=True)
        self.assertStatus(self.slot2, "full")
        self.assertStatus(self.slot, "open")
        self.assertStatus(self.activity, "open")


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
            preparation=timedelta(hours=1), initiative=self.initiative, review=False
        )
        self.review_activity = self.factory.create(
            preparation=timedelta(hours=4), initiative=self.initiative, review=True
        )

        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()
        self.review_activity.refresh_from_db()

    def test_initial_added_through_admin(self):
        mail.outbox = []
        participant = self.participant_factory.create(
            activity=self.review_activity,
            user=BlueBottleUserFactory.create(),
            as_user=self.admin_user,
        )
        SlotParticipantFactory.create(
            slot=self.activity.slots.get(), participant=participant
        )
        self.assertEqual(participant.status, "accepted")

        self.assertEqual(len(mail.outbox), 1)

        self.assertEqual(
            mail.outbox[0].subject,
            'You have been added to the activity "{}" 🎉'.format(
                self.review_activity.title
            ),
        )
        self.assertTrue(
            self.review_activity.followers.filter(user=participant.user).exists()
        )
        prep = participant.preparation_contributions.first()
        self.assertEqual(prep.value, self.review_activity.preparation)
        self.assertEqual(prep.status, "succeeded")

    def test_initial_removed_through_admin(self):
        mail.outbox = []

        participant = self.participant_factory.create(
            activity=self.review_activity,
            user=BlueBottleUserFactory.create(),
            as_user=self.admin_user,
        )
        SlotParticipantFactory.create(
            slot=self.activity.slots.get(), participant=participant
        )
        mail.outbox = []
        participant.states.remove()
        participant.execute_triggers(user=self.admin_user, send_messages=True)
        participant.save()

        self.assertEqual(participant.status, "removed")

        self.assertEqual(len(mail.outbox), 2)

        self.assertEqual(
            mail.outbox[0].subject,
            'You have been removed as participant for the activity "{}"'.format(
                self.review_activity.title
            ),
        )
        self.assertEqual(
            mail.outbox[1].subject,
            'A participant has been removed from your activity "{}"'.format(
                self.review_activity.title
            ),
        )

    def test_accept(self):
        user = BlueBottleUserFactory.create()
        participant = self.participant_factory.create(
            activity=self.review_activity, user=user, as_user=user
        )
        SlotParticipantFactory.create(
            slot=self.activity.slots.get(), participant=participant
        )

        mail.outbox = []
        participant.states.accept(save=True)

        self.assertEqual(participant.status, "accepted")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'You have been selected for the activity "{}" 🎉'.format(
                self.review_activity.title
            ),
        )
        prep = participant.preparation_contributions.first()
        self.assertEqual(prep.value, self.review_activity.preparation)
        self.assertEqual(prep.status, "succeeded")

    def test_no_review_fill(self):
        participants = self.participant_factory.create_batch(
            self.activity.capacity, activity=self.activity
        )
        for participant in participants:
            SlotParticipantFactory.create(
                slot=self.activity.slots.get(), participant=participant
            )

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "full")

    def test_no_review_fill_cancel(self):
        participants = self.participant_factory.create_batch(
            self.activity.capacity, activity=self.activity
        )
        for participant in participants:
            SlotParticipantFactory.create(
                slot=self.activity.slots.get(), participant=participant
            )

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, "full")
        self.activity.states.cancel(save=True)

        self.assertEqual(self.activity.status, "cancelled")

    def test_review_fill(self):
        participants = self.participant_factory.create_batch(
            self.review_activity.capacity,
            activity=self.review_activity,
            user=BlueBottleUserFactory.create(),
            as_relation="user",
        )
        for participant in participants:
            SlotParticipantFactory.create(
                slot=self.review_activity.slots.get(), participant=participant
            )

        self.review_activity.refresh_from_db()

        self.assertEqual(self.activity.status, "open")

        for participant in participants:
            participant.states.accept(save=True)

        self.review_activity.refresh_from_db()

        self.assertEqual(self.review_activity.status, "full")

    def test_remove(self):
        self.participants = self.participant_factory.create_batch(
            self.activity.capacity, activity=self.activity
        )
        for participant in self.participants:
            SlotParticipantFactory.create(
                slot=self.activity.slots.get(), participant=participant
            )

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, "full")
        mail.outbox = []
        participant = self.participants[0]
        participant.states.remove(save=True)

        self.assertEqual(
            participant.contributions.exclude(
                timecontribution__contribution_type="preparation"
            )
            .get()
            .status,
            "failed",
        )
        prep = participant.preparation_contributions.first()
        self.assertEqual(prep.value, self.activity.preparation)
        self.assertEqual(prep.status, "failed")

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'open')

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            'You have been removed as participant for the activity "{}"'.format(
                self.activity.title
            ),
        )
        self.assertEqual(
            mail.outbox[1].subject,
            'A participant has been removed from your activity "{}"'.format(
                self.activity.title
            ),
        )
        self.assertFalse(
            self.activity.followers.filter(user=self.participants[0].user).exists()
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

            SlotParticipantFactory.create(
                slot=self.activity.slots.get(), participant=participant
            )
            self.participants.append(participant)

        mail.outbox = []
        participant = self.participants[0]
        participant.states.reject(save=True)

        self.assertEqual(
            participant.contributions.exclude(
                timecontribution__contribution_type="preparation"
            )
            .get()
            .status,
            "failed",
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'You have not been selected for the activity "{}"'.format(
                self.review_activity.title
            ),
        )
        self.assertFalse(
            self.review_activity.followers.filter(user=participant.user).exists()
        )


class DateParticipantTriggerTestCase(ParticipantTriggerTestCase, BluebottleTestCase):
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory

    def test_type(self):
        participant = self.participant_factory.create(activity=self.review_activity)
        SlotParticipantFactory.create(
            participant=participant, slot=self.review_activity.slots.get()
        )
        self.assertEqual(
            participant.contributions.exclude(
                timecontribution__contribution_type="preparation"
            )
            .get()
            .contribution_type,
            "date",
        )

    def test_reaccept(self):
        self.test_remove()

        self.participants[0].states.accept(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "full")

        self.assertEqual(self.participants[0].contributions.first().status, "new")

        self.assertEqual(self.participants[0].contributions.last().status, "succeeded")
        self.assertTrue(
            self.activity.followers.filter(user=self.participants[0].user).exists()
        )

    def test_initial_no_review(self):
        mail.outbox = []
        user = BlueBottleUserFactory.create()
        participant = self.participant_factory.create(
            activity=self.activity, user=user, as_user=user
        )
        SlotParticipantFactory(
            slot=self.activity.slots.get(), participant=participant, as_user=user
        )

        self.assertEqual(participant.status, "accepted")
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            'A participant has registered for a time slot for your activity "{}"'.format(
                self.activity.title
            ),
        )
        self.assertTrue(self.activity.followers.filter(user=participant.user).exists())
        self.assertEqual(
            self.activity.accepted_participants.get()
            .contributions.exclude(timecontribution__contribution_type="preparation")
            .get()
            .status,
            "new",
        )
        prep = participant.preparation_contributions.first()
        self.assertEqual(prep.value, self.activity.preparation)
        self.assertEqual(prep.status, "succeeded")

    def test_initial_review(self):
        mail.outbox = []
        user = BlueBottleUserFactory.create()
        participant = self.participant_factory.create(
            activity=self.review_activity, user=user, as_user=user
        )
        SlotParticipantFactory(
            slot=self.review_activity.slots.get(), participant=participant
        )

        self.assertEqual(participant.status, "new")
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[1].subject,
            'You have a new participant for your activity "{}" 🎉'.format(
                self.review_activity.title
            ),
        )
        self.assertTrue(
            self.review_activity.followers.filter(user=participant.user).exists()
        )
        self.assertEqual(
            participant.contributions.exclude(
                timecontribution__contribution_type="preparation"
            )
            .get()
            .status,
            "new",
        )
        prep = participant.preparation_contributions.first()
        self.assertEqual(prep.value, self.review_activity.preparation)
        self.assertEqual(prep.status, "new")


class SlotParticipantTriggerTestCase(BluebottleTestCase):
    def setUp(self):
        self.user = BlueBottleUserFactory.create()
        self.initiative = InitiativeFactory.create()
        self.activity = DateActivityFactory.create(
            slots=[], capacity=None, initiative=self.initiative
        )
        self.slot1 = DateActivitySlotFactory.create(activity=self.activity, capacity=2)
        self.slot2 = DateActivitySlotFactory.create(activity=self.activity, capacity=1)

        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)
        self.activity.refresh_from_db()
        self.participant = DateParticipantFactory.create(activity=self.activity)

    def assertStatus(self, obj, status):
        obj.refresh_from_db()
        self.assertEqual(obj.status, status)

    def test_apply(self):
        self.assertEqual(self.participant.slot_participants.count(), 0)
        slot_participant = SlotParticipantFactory.create(
            slot=self.slot1, participant=self.participant
        )
        self.assertEqual(self.participant.slot_participants.count(), 1)
        self.assertStatus(slot_participant, "registered")

    def test_withdraw_from_slot(self):
        slot_participant = SlotParticipantFactory.create(slot=self.slot1, participant=self.participant)
        slot_participant.states.withdraw(save=True)

        self.assertStatus(slot_participant, "withdrawn")
        self.assertStatus(slot_participant.contributions.first(), "failed")

    def test_withdraw_from_slot_finish(self):
        slot_participant = SlotParticipantFactory.create(
            slot=self.slot1, participant=self.participant
        )
        slot_participant.states.withdraw(save=True)

        self.slot1.start = now() - timedelta(days=2)
        self.slot1.save()

        slot_participant.refresh_from_db()

        self.assertStatus(slot_participant, "withdrawn")
        self.assertStatus(slot_participant.contributions.first(), "failed")

    def test_withdraw_from_all_slots(self):
        slot_participant1 = SlotParticipantFactory.create(slot=self.slot1, participant=self.participant)
        slot_participant2 = SlotParticipantFactory.create(slot=self.slot2, participant=self.participant)

        slot_participant1.states.withdraw(save=True)
        self.assertStatus(self.participant, 'accepted')
        self.assertStatus(slot_participant1, 'withdrawn')

        slot_participant2.states.withdraw(save=True)
        self.assertStatus(slot_participant2, 'withdrawn')

        self.assertFalse(
            self.participant.activity.followers.filter(
                user=self.participant.user
            ).exists()
        )

        slot_participant1.states.reapply(save=True)

        self.assertStatus(self.participant, 'accepted')
        self.assertStatus(slot_participant1, 'registered')

        self.assertTrue(
            self.participant.activity.followers.filter(
                user=self.participant.user
            ).exists()
        )

        slot_participant2.states.reapply(save=True)
        self.assertStatus(self.participant, "accepted")
        self.assertStatus(slot_participant2, "registered")

    def test_remove_from_all_slots(self):
        slot_participant1 = SlotParticipantFactory.create(slot=self.slot1, participant=self.participant)
        slot_participant2 = SlotParticipantFactory.create(slot=self.slot2, participant=self.participant)

        slot_participant1.states.remove(save=True)
        self.assertStatus(self.participant, 'accepted')
        self.assertStatus(slot_participant1, 'removed')

        slot_participant2.states.remove(save=True)
        self.assertStatus(self.participant, 'accepted')
        self.assertStatus(slot_participant2, 'removed')

        self.assertFalse(
            self.participant.activity.followers.filter(
                user=self.participant.user
            ).exists()
        )

        slot_participant1.states.accept(save=True)

        self.assertStatus(self.participant, 'accepted')
        self.assertStatus(slot_participant1, 'registered')

        self.assertTrue(
            self.participant.activity.followers.filter(
                user=self.participant.user
            ).exists()
        )

        slot_participant2.states.accept(save=True)
        self.assertStatus(self.participant, "accepted")
        self.assertStatus(slot_participant2, "registered")

    def test_fill_slot(self):
        SlotParticipantFactory.create(slot=self.slot1, participant=self.participant)
        self.assertStatus(self.slot1, "open")
        participant2 = DateParticipantFactory.create(activity=self.activity)
        SlotParticipantFactory.create(slot=self.slot1, participant=participant2)
        self.assertStatus(self.slot1, 'full')
        self.assertStatus(self.activity, 'open')
        SlotParticipantFactory.create(slot=self.slot2, participant=self.participant)
        self.assertStatus(self.slot2, 'full')
        self.assertStatus(self.activity, 'full')

    def test_do_not_fill_withdrawn(self):
        withdrawn = SlotParticipantFactory.create(
            slot=self.slot1, participant=self.participant
        )
        withdrawn.states.withdraw(save=True)
        self.assertStatus(self.slot1, "open")
        participant2 = DateParticipantFactory.create(activity=self.activity)

        SlotParticipantFactory.create(slot=self.slot1, participant=participant2)
        self.assertStatus(self.slot1, "open")
        self.assertStatus(self.activity, "open")

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

    def test_extend_slot_unfills(self):
        self.assertStatus(self.activity, 'open')
        SlotParticipantFactory.create(slot=self.slot1, participant=self.participant)
        participant2 = DateParticipantFactory.create(activity=self.activity)
        SlotParticipantFactory.create(slot=self.slot1, participant=participant2)
        participant2 = DateParticipantFactory.create(activity=self.activity)
        SlotParticipantFactory.create(slot=self.slot2, participant=participant2)
        self.assertStatus(self.slot1, 'full')
        self.assertStatus(self.slot2, 'full')
        self.assertStatus(self.activity, 'full')

        self.slot1.capacity = 10
        self.slot1.save()
        self.assertStatus(self.slot1, 'open')
        self.assertStatus(self.activity, 'open')

    def test_cancel_open_slot_fills(self):
        self.assertStatus(self.activity, 'open')
        self.assertStatus(self.slot1, 'open')
        SlotParticipantFactory.create(slot=self.slot2, participant=self.participant)
        self.assertStatus(self.slot1, 'open')
        self.assertStatus(self.slot2, 'full')
        self.assertStatus(self.activity, 'open')
        self.slot1.states.cancel(save=True)
        self.assertStatus(self.activity, 'full')
        self.slot3 = DateActivitySlotFactory.create(activity=self.activity)
        self.assertStatus(self.activity, 'open')
        self.slot3.delete()
        self.assertStatus(self.activity, 'full')

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


class PeriodicActivitySlotTriggerTestCase(TriggerTestCase):
    factory = PeriodicSlotFactory

    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=[self.factory._meta.model.__name__.lower()]
        )

        self.initiative = InitiativeFactory.create(
            status='approved'
        )
        self.activity = PeriodicActivityFactory.create(
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=20),
            initiative=self.initiative,
            status="open",
            review=False
        )
        start = make_aware(
            datetime.combine(self.activity.start, datetime.min.time()),
            get_current_timezone()
        )

        self.defaults = {
            'activity': self.activity,
            'start': start,
            'end': start + relativedelta(**{self.activity.period: 1}),
        }

        PeriodicRegistrationFactory.create_batch(
            3, activity=self.activity, status='accepted'
        )
        PeriodicRegistrationFactory.create_batch(3, activity=self.activity, status='rejected')

    def test_initiate(self):
        self.model = self.factory.build(**self.defaults)

        with self.execute():
            self.assertEffect(CreatePeriodicParticipantsEffect)

            self.model.save()

        self.assertEqual(self.model.participants.count(), 3)

        for participant in self.model.participants.all():
            self.assertEqual(participant.status, 'new')

    def test_finish(self):
        self.create()
        self.model.states.start(save=True)
        self.model.states.finish()

        with self.execute():
            self.assertEffect(CreateNextSlotEffect)
            self.assertTransitionEffect(
                PeriodicParticipantStateMachine.succeed, self.model.participants.first()
            )

            self.model.save()

        for participant in self.model.participants.all():
            self.assertEqual(participant.status, 'succeeded')

        self.assertEqual(self.activity.slots.count(), 2)
        next_slot = self.activity.slots.get(status='running')

        self.assertEqual(next_slot.start, self.model.end)
        self.assertEqual(
            next_slot.end,
            self.model.end + relativedelta(**{self.activity.period: 1}),
        )


class RegistrationTriggerTestBase:
    factory = None
    activity_factory = None
    user_joined_notification = None

    def setUp(self):
        self.user = BlueBottleUserFactory.create()
        self.staff = BlueBottleUserFactory.create(is_staff=True)
        self.manager = BlueBottleUserFactory.create()
        self.activity = self.activity_factory.create(
            owner=self.manager,
            status="open",
            review=False
        )

    def test_join(self):
        user = BlueBottleUserFactory.create()
        self.model = self.factory.build(
            activity=self.activity,
            user=user,
        )
        with self.execute(user=user):
            self.assertNotificationEffect(
                self.user_joined_notification
            )
            self.assertNotificationEffect(
                ManagerRegistrationCreatedNotification
            )

    def test_apply(self):
        self.activity.review = True
        self.activity.save()
        self.model = PeriodicRegistrationFactory.build(
            activity=self.activity,
            user=self.user,
        )
        with self.execute(user=self.user):
            self.assertNotificationEffect(
                PeriodicUserAppliedNotification
            )
            self.assertNotificationEffect(
                ManagerRegistrationCreatedReviewNotification
            )

    def test_added_by_staff(self):
        self.model = PeriodicRegistrationFactory.build(
            activity=self.activity,
            user=self.user,
        )
        with self.execute(user=self.staff):
            self.assertNotificationEffect(
                ParticipantAddedNotification
            )
            self.assertNotificationEffect(
                ManagerParticipantAddedOwnerNotification
            )

    def test_added_by_staff_is_active(self):
        self.user.is_active = False
        self.user.save()

        self.model = PeriodicRegistrationFactory.build(
            activity=self.activity,
            user=self.user,
        )
        with self.execute(user=self.staff):
            self.assertNoNotificationEffect(
                ParticipantAddedNotification
            )
            self.assertNotificationEffect(
                InactiveParticipantAddedNotification
            )
            self.assertNotificationEffect(
                ManagerParticipantAddedOwnerNotification
            )

    def test_accept(self):
        self.test_apply()
        self.model.states.accept()
        with self.execute(user=self.manager):
            self.assertNotificationEffect(
                UserRegistrationAcceptedNotification
            )

    def test_reject(self):
        self.test_apply()
        self.model.states.reject()
        with self.execute(user=self.manager):
            self.assertNotificationEffect(
                UserRegistrationRejectedNotification
            )


class PeriodicRegistrationTriggersTestCase(RegistrationTriggerTestBase, TriggerTestCase):

    factory = PeriodicRegistrationFactory
    activity_factory = PeriodicActivityFactory
    user_joined_notification = PeriodicUserJoinedNotification

    def test_user_stops(self):
        self.test_join()
        self.model.states.stop()
        with self.execute(user=self.user):
            self.assertNotificationEffect(
                UserRegistrationStoppedNotification
            )

    def test_user_restarts(self):
        self.test_user_stops()
        self.model.states.start()
        with self.execute(user=self.user):
            self.assertNotificationEffect(
                UserRegistrationRestartedNotification
            )

    def test_manager_stops(self):
        self.test_join()
        self.model.states.stop()
        with self.execute(user=self.manager):
            self.assertNotificationEffect(
                UserRegistrationStoppedNotification
            )

    def test_manager_restarts(self):
        self.test_manager_stops()
        self.model.states.start()
        with self.execute(user=self.manager):
            self.assertNotificationEffect(
                UserRegistrationRestartedNotification
            )


class ScheduleRegistrationTriggersTestCase(RegistrationTriggerTestBase, TriggerTestCase):

    factory = ScheduleRegistrationFactory
    activity_factory = ScheduleActivityFactory
    user_joined_notification = ScheduleUserJoinedNotification

    def test_manager_schedules_slot(self):
        self.test_join()
        slot = ScheduleSlotFactory.create(
            activity=self.activity,
        )
        registration = self.model
        registration.save()
        self.model = registration.participants.first()
        self.model.slot = slot
        with self.execute(user=self.manager):
            self.assertNotificationEffect(
                UserScheduledNotification
            )
