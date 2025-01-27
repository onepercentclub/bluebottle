from datetime import timedelta, date

from django.core import mail
from django.utils.timezone import now

from bluebottle.initiatives.tests.factories import (
    InitiativeFactory,
    InitiativePlatformSettingsFactory,
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.models import TimeContribution
from bluebottle.time_based.tests.factories import (
    DeadlineActivityFactory,
    DeadlineParticipantFactory,
    DeadlineRegistrationFactory,
    PeriodicActivityFactory,
    PeriodicRegistrationFactory,
    ScheduleRegistrationFactory,
    ScheduleActivityFactory,
    TeamFactory,
    TeamMemberFactory,
)


class ParticipantTriggerTestCase:
    expected_status = "succeeded"
    expected_contribution_status = "succeeded"
    expected_preparation_status = "succeeded"

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
            review=False,
            capacity=4,
            registration_deadline=None,
            preparation=timedelta(hours=1),
        )
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.activity.states.publish(save=True)

        mail.outbox = []

    def test_initial(self):
        self.register()

        self.assertEqual(self.participant.status, self.expected_status)
        self.assertTrue(
            self.activity.followers.filter(user=self.participant.user).exists()
        )

        contribution = self.participant.contributions.get(
            timecontribution__contribution_type="period"
        )
        self.assertEqual(contribution.status, self.expected_contribution_status)
        self.assertEqual(contribution.value, self.activity.duration)

        preparation_contribution = self.participant.preparation_contributions.first()
        self.assertEqual(preparation_contribution.value, self.activity.preparation)
        self.assertEqual(
            preparation_contribution.status, self.expected_preparation_status
        )

    def test_withdraw(self):
        self.test_initial()
        mail.outbox = []
        self.participant.states.withdraw(save=True)
        self.assertEqual(self.participant.status, "withdrawn")
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            'You have withdrawn from the activity "{}"'.format(self.activity.title),
        )
        self.assertEqual(
            mail.outbox[1].subject,
            'A participant has withdrawn from your activity "{}"'.format(self.activity.title),
        )

        self.assertFalse(
            self.activity.followers.filter(user=self.participant.user).exists()
        )
        contribution = self.participant.contributions.get(
            timecontribution__contribution_type="period"
        )
        self.assertEqual(contribution.status, "failed")

        preparation_contribution = self.participant.preparation_contributions.first()
        self.assertEqual(preparation_contribution.status, "failed")

    def test_fill(self):
        self.activity.capacity = 1
        self.activity.save()

        self.test_initial()

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "full")

    def test_withdraw_unfill(self):
        self.activity.capacity = 1

        self.test_withdraw()

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "open")

    def test_remove_unfill(self):
        self.activity.capacity = 1
        self.activity.save()

        self.test_remove()

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "open")

    def test_reapply(self):
        self.test_withdraw()
        self.participant.states.reapply(save=True)
        self.assertEqual(self.participant.status, self.expected_status)

        self.assertTrue(
            self.activity.followers.filter(user=self.participant.user).exists()
        )

        contribution = self.participant.contributions.get(
            timecontribution__contribution_type="period"
        )
        self.assertEqual(contribution.status, self.expected_contribution_status)

        preparation_contribution = self.participant.preparation_contributions.first()
        self.assertEqual(
            preparation_contribution.status, self.expected_contribution_status
        )

    def test_remove(self):
        self.test_initial()

        mail.outbox = []
        self.participant.states.remove(save=True)
        self.assertEqual(self.participant.status, "removed")
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

        self.assertFalse(
            self.activity.followers.filter(user=self.participant.user).exists()
        )
        contribution = self.participant.contributions.get(
            timecontribution__contribution_type="period"
        )
        self.assertEqual(contribution.status, "failed")

        preparation_contribution = self.participant.preparation_contributions.first()
        self.assertEqual(preparation_contribution.status, "failed")

    def test_readd(self):
        self.test_remove()
        mail.outbox = []
        self.participant.states.readd(save=True)
        self.assertEqual(self.participant.status, self.expected_status)

        self.assertTrue(
            self.activity.followers.filter(user=self.participant.user).exists()
        )

        contribution = self.participant.contributions.get(
            timecontribution__contribution_type="period"
        )
        self.assertEqual(contribution.status, self.expected_contribution_status)

        preparation_contribution = self.participant.preparation_contributions.first()
        self.assertEqual(
            preparation_contribution.status, self.expected_contribution_status
        )

    def test_reject(self):
        self.test_initial()
        self.participant.states.reject(save=True)
        self.assertEqual(self.participant.status, "rejected")

        self.assertFalse(
            self.activity.followers.filter(user=self.participant.user).exists()
        )
        contribution = self.participant.contributions.get(
            timecontribution__contribution_type="period"
        )
        self.assertEqual(contribution.status, "failed")

        preparation_contribution = self.participant.preparation_contributions.first()
        self.assertEqual(preparation_contribution.status, "failed")

    def test_accept(self):
        self.test_reject()

        self.participant.states.accept(save=True)
        self.assertEqual(self.participant.status, self.expected_status)

        self.assertTrue(
            self.activity.followers.filter(user=self.participant.user).exists()
        )

        contribution = self.participant.contributions.get(
            timecontribution__contribution_type="period"
        )
        self.assertEqual(contribution.status, self.expected_contribution_status)

        preparation_contribution = self.participant.preparation_contributions.first()
        self.assertEqual(
            preparation_contribution.status, self.expected_contribution_status
        )


class DeadlineParticipantTriggerCase(ParticipantTriggerTestCase, BluebottleTestCase):
    activity_factory = DeadlineActivityFactory

    def create(self, user=None, as_user=None):
        if not user:
            user = BlueBottleUserFactory.create()

        if not as_user:
            as_user = user

        self.participant = DeadlineParticipantFactory.create(
            activity=self.activity, user=user, as_user=as_user
        )

    def register(self):
        user = BlueBottleUserFactory.create()
        registration = DeadlineRegistrationFactory.create(
            activity=self.activity,
            user=user,
            as_user=user
        )
        self.participant = registration.participants.get()

    def test_initial_added_through_admin(self):
        mail.outbox = []
        self.create(as_user=self.admin_user)
        self.assertEqual(self.participant.status, self.expected_status)

        self.assertEqual(self.participant.registration.status, "accepted")

        self.assertEqual(len(mail.outbox), 1)

        self.assertEqual(
            mail.outbox[0].subject,
            'You have been added to the activity "{}" 🎉'.format(self.activity.title),
        )

    def test_initial_removed_through_admin(self):
        self.create(as_user=self.admin_user)
        mail.outbox = []

        self.participant.states.remove()
        self.participant.execute_triggers(user=self.admin_user, send_messages=True)
        self.participant.save()

        self.assertEqual(self.participant.status, "removed")
        self.assertEqual(self.participant.contributions.first().status, "failed")

        self.assertEqual(len(mail.outbox), 2)

        self.assertEqual(
            mail.outbox[-2].subject,
            'You have been removed as participant for the activity "{}"'.format(
                self.activity.title
            ),
        )
        self.assertEqual(
            mail.outbox[-1].subject,
            'A participant has been removed from your activity "{}"'.format(
                self.activity.title
            ),
        )

    def test_initial_succeed_activity(self):
        self.activity.deadline = date.today() - timedelta(days=4)
        self.activity.save()

        self.create(as_user=self.admin_user)

        self.assertEqual(self.participant.status, "succeeded")
        self.assertEqual(self.participant.contributions.first().status, "succeeded")
        self.assertEqual(self.participant.activity.status, "succeeded")

    def test_expire(self):
        self.test_initial_succeed_activity()

        self.participant.states.withdraw(save=True)
        self.assertEqual(self.participant.status, "withdrawn")
        self.assertEqual(self.participant.contributions.first().status, "failed")
        self.assertEqual(self.participant.activity.status, "expired")


class PeriodicParticipantTriggerCase(ParticipantTriggerTestCase, BluebottleTestCase):
    activity_factory = PeriodicActivityFactory

    def register(self):
        user = BlueBottleUserFactory.create()
        self.registration = PeriodicRegistrationFactory.create(
            activity=self.activity,
            user=user,
            as_user=user
        )
        self.registration.refresh_from_db()
        self.participant = self.registration.participants.first()
        slot = self.participant.slot
        slot.states.start(save=True)
        slot.states.finish(save=True)
        self.participant.refresh_from_db()

    def test_single_preparation_contribution(self):
        self.register()
        preparation = TimeContribution.objects.get(
            contributor__activity=self.activity, contribution_type="preparation"
        )

        self.assertEqual(preparation.contributor, self.participant)

    def test_remove_unfill(self):
        # Skip this test for periodic activity
        pass

    def test_fill_unfill(self):
        self.activity.capacity = 1
        self.activity.save()
        self.register()
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "full")
        self.registration.states.stop(save=True)
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "open")


class ScheduleParticipantTriggerCase(ParticipantTriggerTestCase, BluebottleTestCase):
    activity_factory = ScheduleActivityFactory
    expected_status = "accepted"
    expected_contribution_status = "new"

    def register(self):
        user = BlueBottleUserFactory.create()
        self.registration = ScheduleRegistrationFactory.create(
            activity=self.activity,
            user=user,
            as_user=user
        )
        self.participant = self.registration.participants.first()
        self.participant.save()

    def schedule(self, when):
        slot = self.participant.slot
        slot.start = when
        slot.save()
        self.participant.refresh_from_db()

    def test_initial(self):
        super().test_initial()
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, "accepted")

    def test_fill(self):
        self.activity.capacity = 1
        self.activity.save()

        self.test_initial()

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "full")

    def test_withdraw_unfill(self):
        self.activity.capacity = 1
        self.activity.save()

        self.test_withdraw()

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "open")

    def test_remove_unfill(self):
        self.activity.capacity = 1
        self.activity.save()

        self.test_remove()

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "open")

    def test_schedule(self):
        self.register()
        self.schedule(now() + timedelta(days=1))
        contribution = self.participant.contributions.get(
            timecontribution__contribution_type="period"
        )
        self.assertEqual(contribution.status, "new")
        preparation = self.participant.preparation_contributions.first()
        self.assertEqual(preparation.status, "succeeded")

        self.assertEqual(self.participant.status, "scheduled")

    def test_schedule_passed(self):
        self.register()
        self.schedule(now() - timedelta(days=4))

        self.participant.refresh_from_db()
        self.assertEqual(self.participant.status, "succeeded")

        contribution = self.participant.contributions.get(
            timecontribution__contribution_type="period"
        )
        self.assertEqual(contribution.status, "succeeded")
        preparation = self.participant.preparation_contributions.first()
        self.assertEqual(preparation.status, "succeeded")

    def test_initial_succeed_activity(self):
        self.activity.deadline = date.today() - timedelta(days=4)
        self.activity.save()

        self.assertEqual(self.activity.status, "expired")

        self.register()
        self.schedule(now() - timedelta(days=2))

        self.assertEqual(self.participant.status, "succeeded")
        self.assertEqual(self.participant.contributions.first().status, "succeeded")
        self.assertEqual(self.participant.activity.status, "succeeded")

    def test_expire(self):
        self.test_initial_succeed_activity()

        self.participant.states.remove(save=True)

        self.assertEqual(self.participant.status, "removed")
        self.assertEqual(self.participant.contributions.first().status, "failed")
        self.assertEqual(self.participant.activity.status, "expired")


class TeamScheduleParticipantTriggerTestCase(BluebottleTestCase):
    def setUp(self):
        self.captain = BlueBottleUserFactory.create()
        initiative = InitiativeFactory.create()
        self.activity = ScheduleActivityFactory.create(
            team_activity=True, initiative=initiative
        )
        initiative.states.submit()
        initiative.states.approve(save=True)
        self.activity.states.publish(save=True)

    def create(self):
        self.team = TeamFactory.create(activity=self.activity, user=self.captain)
        self.team_member = TeamMemberFactory.create(team=self.team)
        self.participant = self.team_member.participants.get()

    def schedule(self, when):
        slot = self.team.slots.get()

        slot.start = when
        slot.duration = timedelta(hours=2)
        slot.is_online = True

        slot.save()

        self.participant.refresh_from_db()

    def test_initiate(self):
        self.create()
        self.assertEqual(self.participant.status, "accepted")

        self.assertEqual(self.participant.contributions.get().status, "new")

    def test_schedule(self):
        self.create()
        self.schedule(now())

        self.participant.refresh_from_db()
        self.assertEqual(self.participant.status, "scheduled")

        self.assertEqual(self.participant.contributions.get().status, "new")

    def test_succeed(self):
        self.create()
        self.schedule(now())
        self.schedule(now() - timedelta(days=2))

        self.participant.refresh_from_db()
        self.assertEqual(self.participant.status, "succeeded")

        self.assertEqual(self.participant.contributions.get().status, "succeeded")

    def test_initial_succeed_activity(self):
        self.activity.deadline = date.today() - timedelta(days=4)
        self.activity.save()

        self.assertEqual(self.activity.status, "expired")

        self.create()
        self.schedule(now() - timedelta(days=2))

        self.assertEqual(self.participant.status, "succeeded")
        self.assertEqual(self.participant.contributions.first().status, "succeeded")
        self.assertEqual(self.participant.activity.status, "succeeded")

    def test_expire(self):
        self.test_initial_succeed_activity()

        self.team_member.states.remove(save=True)
        self.participant.states.remove(save=True)
        self.assertEqual(self.participant.status, "removed")
        self.assertEqual(self.participant.contributions.first().status, "failed")
        self.assertEqual(self.participant.activity.status, "expired")
