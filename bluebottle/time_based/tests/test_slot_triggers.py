from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.core import mail
from django.utils.timezone import now

from bluebottle.initiatives.tests.factories import (
    InitiativeFactory,
    InitiativePlatformSettingsFactory,
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import (
    PeriodicActivityFactory,
    PeriodicRegistrationFactory,
    ScheduleActivityFactory,
    ScheduleParticipantFactory,
    ScheduleSlotFactory,
    TeamScheduleRegistrationFactory,
    TeamMemberFactory, DateActivityFactory, DateActivitySlotFactory, DateParticipantFactory,
)


class PeriodicSlotTriggerTestCase(BluebottleTestCase):
    activity_factory = PeriodicActivityFactory

    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=[self.activity_factory._meta.model.__name__.lower()]
        )
        self.admin_user = BlueBottleUserFactory.create(is_staff=True)
        self.user = BlueBottleUserFactory()

        self.initiative = InitiativeFactory(owner=self.user)

        self.activity = self.activity_factory.create(
            initiative=self.initiative,
            period="weeks",
            registration_deadline=None,
        )
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.activity.states.publish(save=True)

        mail.outbox = []

    def register(self):
        user = BlueBottleUserFactory.create()
        self.registration = PeriodicRegistrationFactory.create(
            activity=self.activity,
            user=user,
            as_user=user
        )

    @property
    def first_slot(self):
        return self.activity.slots.first()

    def test_initial(self):
        self.register()
        self.assertEqual(self.first_slot.status, "new")
        self.assertEqual(self.first_slot.participants.get().status, "new")

    def test_initial_review(self):
        self.activity.review = True
        self.activity.save()

        self.register()
        self.assertEqual(self.first_slot.status, "new")
        self.assertEqual(self.first_slot.participants.count(), 0)

    def test_start(self):
        self.register()
        self.first_slot.states.start(save=True)
        self.assertEqual(self.first_slot.status, "running")
        self.assertEqual(self.first_slot.participants.get().status, "new")

    def test_finish(self):
        self.test_start()
        self.first_slot.states.finish(save=True)

        self.assertEqual(self.first_slot.status, "finished")
        self.assertEqual(self.first_slot.participants.get().status, "succeeded")

        self.assertTrue(self.activity.slots.count(), 2)

        second_slot = self.activity.slots.all()[1]
        self.assertEqual(second_slot.status, "running")

        self.assertEqual(second_slot.participants.get().status, "new")
        self.assertEqual(second_slot.participants.get().registration, self.registration)
        self.assertEqual(second_slot.participants.get().registration, self.registration)

        self.assertEqual(second_slot.start, self.first_slot.end)
        self.assertEqual(
            second_slot.end,
            self.first_slot.end + relativedelta(**{self.activity.period: 1}),
        )


class ScheduleSlotTriggerTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=["scheduleactivity"]
        )
        self.admin_user = BlueBottleUserFactory.create(is_staff=True)
        self.user = BlueBottleUserFactory()

        self.initiative = InitiativeFactory(owner=self.user)

        self.activity = ScheduleActivityFactory.create(
            initiative=self.initiative, registration_deadline=None, review=False
        )
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.activity.states.publish(save=True)
        self.participant = ScheduleParticipantFactory.create(activity=self.activity)

        mail.outbox = []

    def create(self, duration=timedelta(hours=2), is_online=True, **kwargs):

        self.slot = ScheduleSlotFactory.create(
            activity=self.activity, is_online=is_online, duration=duration, **kwargs
        )
        self.participant.slot = self.slot
        self.participant.save()

    def assertStatus(self, status, obj=None):
        if not obj:
            obj = self.slot

        obj.refresh_from_db()

        self.assertEqual(obj.status, status)

    def test_initial_future(self):
        self.create(start=now() + timedelta(days=2))

        self.assertStatus("new")
        self.assertStatus("scheduled", self.participant)
        self.assertStatus("new", self.participant.contributions.get())

    def test_change_start_finish(self):
        self.create(start=now() + timedelta(days=2))
        self.slot.start = now() - timedelta(days=2)
        self.slot.save()

        self.assertStatus("finished")
        self.assertStatus("succeeded", self.participant)
        self.assertStatus("succeeded", self.participant.contributions.get())

    def test_initial_passed(self):
        self.create(start=now() - timedelta(days=2))

        self.assertStatus("finished")
        self.assertStatus("succeeded", self.participant)
        self.assertStatus("succeeded", self.participant.contributions.get())

    def test_change_start_reopen(self):
        self.create(start=now() - timedelta(days=2))
        self.slot.start = now() + timedelta(days=2)
        self.slot.save()

        self.assertStatus("scheduled")
        self.assertStatus("scheduled", self.participant)
        self.assertStatus("new", self.participant.contributions.get())


class TeamScheduleSlotTriggerTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=["scheduleactivity"]
        )
        self.admin_user = BlueBottleUserFactory.create(is_staff=True)
        self.user = BlueBottleUserFactory()

        self.initiative = InitiativeFactory(owner=self.user)

        self.activity = ScheduleActivityFactory.create(
            initiative=self.initiative,
            registration_deadline=None,
            review=False,
            team_activity="teams",
        )
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.activity.states.publish(save=True)
        self.registration = TeamScheduleRegistrationFactory.create(
            activity=self.activity
        )
        self.slot = self.registration.team.slots.first()

        self.members = TeamMemberFactory.create_batch(3, team=self.registration.team)

        mail.outbox = []

    def assertStatus(self, status, obj=None):
        if not obj:
            obj = self.slot

        obj.refresh_from_db()

        self.assertEqual(obj.status, status)

    def test_initial_future(self):
        self.assertStatus("new")
        self.assertStatus("accepted", self.registration.team)

    def test_change_start_finish(self):
        self.slot.start = now() - timedelta(days=2)
        self.slot.save()

        self.assertStatus("finished")
        self.assertStatus("succeeded", self.registration.team)

        self.assertEqual(len(mail.outbox), 4)
        for message in mail.outbox:
            self.assertTrue(
                message.recipients()[0]
                in [
                    member.user.email
                    for member in self.registration.team.team_members.all()
                ]
            )
            self.assertTrue(
                message.subject,
                f'The date or location for your team has been changed for the activity "{self.activity.title}."',
            )

    def test_change_start_reopen(self):
        self.test_change_start_finish()

        self.slot.start = now() + timedelta(days=2)
        self.slot.save()

        self.assertStatus("scheduled")
        self.assertStatus("scheduled", self.registration.team)


class DateActivitySlotTriggerTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.admin_user = BlueBottleUserFactory.create(is_staff=True)
        self.user = BlueBottleUserFactory()

        self.initiative = InitiativeFactory(owner=self.user)

        self.activity = DateActivityFactory.create(
            initiative=self.initiative,
            registration_deadline=None,
            review=False,
            slots=[]
        )
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.slot1 = DateActivitySlotFactory.create(
            activity=self.activity,
            start=now() + timedelta(days=2),
        )
        self.slot2 = DateActivitySlotFactory.create(
            activity=self.activity,
            start=now() + timedelta(days=3),
        )
        self.activity.states.publish(save=True)
        self.participant = DateParticipantFactory.create(
            activity=self.activity,
            slot=self.slot1,
        )

        self.splitter = DateParticipantFactory.create(
            activity=self.activity,
            slot=self.slot1,
        )
        self.splitter.states.withdraw(save=True)

        mail.outbox = []

    def assertStatus(self, obj, status):
        obj.refresh_from_db()
        self.assertEqual(obj.status, status)

    def test_cancel_future(self):
        self.assertStatus(self.slot1, "open")
        self.assertStatus(self.activity, "open")
        self.assertStatus(self.participant, "accepted")
        self.assertStatus(self.participant.contributions.get(), "new")
        self.assertStatus(self.splitter, "withdrawn")
        self.assertStatus(self.splitter.contributions.get(), "failed")

        self.slot1.states.cancel(save=True)
        self.assertStatus(self.slot1, "cancelled")
        self.assertStatus(self.activity, "open")
        self.assertStatus(self.participant, "cancelled")
        self.assertStatus(self.participant.contributions.get(), "failed")
        self.assertStatus(self.splitter, "withdrawn")
        self.assertStatus(self.splitter.contributions.get(), "failed")

        self.slot1.states.restore(save=True)
        self.assertStatus(self.slot1, "open")
        self.assertStatus(self.activity, "open")
        self.assertStatus(self.participant, "accepted")
        self.assertStatus(self.participant.contributions.get(), "new")
        self.assertStatus(self.splitter, "withdrawn")
        self.assertStatus(self.splitter.contributions.get(), "failed")

    def test_cancel_future_with_past_success(self):
        self.slot2.start = now() - timedelta(days=2)
        self.slot2.save()
        self.assertStatus(self.slot2, "finished")
        self.assertStatus(self.activity, "open")

        self.assertStatus(self.slot1, "open")
        self.assertStatus(self.activity, "open")
        self.assertStatus(self.participant, "accepted")
        self.assertStatus(self.participant.contributions.get(), "new")

        self.slot1.states.cancel(save=True)
        self.assertStatus(self.slot1, "cancelled")
        self.assertStatus(self.activity, "succeeded")
        self.assertStatus(self.participant, "cancelled")
        self.assertStatus(self.participant.contributions.get(), "failed")

        self.slot1.states.restore(save=True)
        self.assertStatus(self.slot1, "open")
        self.assertStatus(self.activity, "open")
        self.assertStatus(self.participant, "accepted")
        self.assertStatus(self.participant.contributions.get(), "new")

    def test_cancel_all_slots(self):
        self.slot1.states.cancel(save=True)
        self.assertStatus(self.slot1, "cancelled")
        self.assertStatus(self.activity, "open")

        self.slot2.states.cancel(save=True)
        self.assertStatus(self.slot2, "cancelled")
        self.assertStatus(self.slot1, "cancelled")
        self.assertStatus(self.activity, "cancelled")

        self.slot1.states.restore(save=True)
        self.assertStatus(self.slot1, "open")
        self.assertStatus(self.activity, "open")

    def test_cancel_past(self):
        self.slot1.start = now() - timedelta(days=2)
        self.slot1.save()

        self.assertStatus(self.slot1, "finished")
        self.assertStatus(self.activity, "open")
        self.assertStatus(self.participant, "succeeded")
        self.assertStatus(self.participant.contributions.get(), "succeeded")
        self.assertStatus(self.splitter, "withdrawn")
        self.assertStatus(self.splitter.contributions.get(), "failed")

        self.slot1.states.cancel(save=True)
        self.assertStatus(self.slot1, "cancelled")
        self.assertStatus(self.activity, "open")
        self.assertStatus(self.participant, "cancelled")
        self.assertStatus(self.participant.contributions.get(), "failed")
        self.assertStatus(self.splitter, "withdrawn")
        self.assertStatus(self.splitter.contributions.get(), "failed")

        self.slot1.states.restore(save=True)
        self.assertStatus(self.slot1, "finished")
        self.assertStatus(self.activity, "open")
        self.assertStatus(self.participant, "succeeded")
        self.assertStatus(self.participant.contributions.get(), "succeeded")
        self.assertStatus(self.splitter, "withdrawn")
        self.assertStatus(self.splitter.contributions.get(), "failed")
