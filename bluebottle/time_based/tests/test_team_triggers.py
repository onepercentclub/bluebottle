from django.core import mail

from bluebottle.initiatives.tests.factories import (
    InitiativeFactory,
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import (
    ScheduleActivityFactory,
    TeamFactory,
    TeamMemberFactory,
    TeamScheduleRegistrationFactory,
)


class TeamTriggerTestCase(BluebottleTestCase):
    def setUp(self):
        self.captain = BlueBottleUserFactory.create()
        initiative = InitiativeFactory.create()
        activity = ScheduleActivityFactory.create(
            team_activity='teams',
            initiative=initiative
        )
        initiative.states.submit()
        initiative.states.approve(save=True)
        activity.states.publish(save=True)

        self.team = TeamFactory.create(activity=activity, user=self.captain)

    def test_initiate(self):
        self.assertEqual(self.team.status, "accepted")

        self.assertEqual(self.team.registration.status, "accepted")
        self.assertEqual(self.team.registration.user, self.captain)

        self.assertEqual(self.team.team_members.get().status, "active")
        self.assertEqual(self.team.team_members.get().user, self.captain)
        self.assertEqual(
            self.team.team_members.get().participants.get().status, "accepted"
        )
        self.assertEqual(
            self.team.team_members.get().participants.get().user, self.captain
        )

    def test_cancel_activity(self):
        self.team.activity.states.cancel(save=True)

        self.team.refresh_from_db()

        self.assertEqual(self.team.status, "cancelled")

        self.assertEqual(self.team.team_members.get().status, "cancelled")
        self.assertEqual(
            self.team.team_members.get().participants.get().status, "cancelled"
        )
        self.assertEqual(
            self.team.team_members.get().participants.get().contributions.get().status,
            "failed",
        )

    def test_withdraw(self):
        self.team.states.withdraw(save=True)
        self.assertEqual(self.team.status, "withdrawn")

        self.assertEqual(self.team.registration.status, "accepted")

        self.assertEqual(self.team.team_members.get().status, "withdrawn")

        self.assertEqual(
            mail.outbox[-1].subject,
            f'A team has withdrawn from your activity "{self.team.activity.title}"',
        )

    def test_reapply(self):
        self.team.states.withdraw(save=True)
        self.team.states.rejoin(save=True)
        self.assertEqual(self.team.team_members.get().status, "active")
        self.assertEqual(self.team.status, "accepted")

        self.assertEqual(self.team.registration.status, "accepted")

        self.assertEqual(self.team.team_members.get().status, "active")

    def test_remove(self):
        mail.outbox = []
        self.team.states.remove(save=True)
        self.assertEqual(self.team.status, "removed")
        print([m.subject for m in mail.outbox])
        self.assertEqual(
            len(mail.outbox),
            2
        )
        self.assertEqual(
            mail.outbox[0].subject,
            f'Your team was removed from the activity "{self.team.activity.title}"',
        )
        self.assertEqual(
            mail.outbox[1].subject,
            f'A team has been removed from your activity "{self.team.activity.title}"',
        )

        self.assertEqual(self.team.registration.status, "accepted")

        self.assertEqual(self.team.team_members.get().status, "removed")
        self.assertEqual(
            self.team.team_members.get().participants.get().status, "removed"
        )
        self.assertEqual(
            self.team.team_members.get().participants.get().contributions.get().status,
            "failed",
        )

    def test_readd(self):
        self.team.states.remove(save=True)
        self.team.states.readd(save=True)

        self.assertEqual(self.team.status, "accepted")
        self.assertEqual(self.team.registration.status, "accepted")
        self.assertEqual(self.team.team_members.get().status, "active")

    def test_reject(self):
        registration = TeamScheduleRegistrationFactory.create()
        team = registration.team
        registration.states.reject(save=True)

        self.assertEqual(team.status, "rejected")
        self.assertEqual(team.registration.status, "rejected")
        self.assertEqual(team.team_members.get().status, "rejected")

    def test_reaccept(self):
        registration = TeamScheduleRegistrationFactory.create()
        team = registration.team
        registration.states.reject(save=True)
        registration.states.accept(save=True)

        self.assertEqual(team.status, "accepted")
        self.assertEqual(registration.status, "accepted")
        self.assertEqual(team.team_members.get().status, "active")


class TeamMemberTriggerTestCase(BluebottleTestCase):
    def setUp(self):
        self.captain = BlueBottleUserFactory.create()
        initiative = InitiativeFactory.create()
        activity = ScheduleActivityFactory.create(
            team_activity=True, initiative=initiative
        )
        initiative.states.submit()
        initiative.states.approve(save=True)
        activity.states.publish(save=True)

        self.team = TeamFactory.create(activity=activity, user=self.captain)
        self.team_member = TeamMemberFactory.create(team=self.team)

    def test_initiate(self):
        self.assertEqual(self.team_member.status, "active")

        self.assertEqual(self.team_member.participants.get().status, "accepted")

        self.assertEqual(
            mail.outbox[-1].subject,
            "Someone has joined your team on Test",
        )

        self.assertEqual(
            mail.outbox[-2].subject,
            f"You are now part of {self.team.user.full_name}'s team on Test",
        )

    def test_withdraw(self):
        self.team_member.states.withdraw(save=True)

        self.assertEqual(self.team_member.status, "withdrawn")
        self.assertEqual(self.team_member.participants.get().status, "withdrawn")

    def test_reapply(self):
        self.team_member.states.withdraw(save=True)
        self.team_member.states.reapply(save=True)

        self.assertEqual(self.team_member.status, "active")
        self.assertEqual(self.team_member.participants.get().status, "accepted")

    def test_remove(self):
        self.team_member.states.remove(save=True)

        self.assertEqual(self.team_member.status, "removed")
        self.assertEqual(self.team_member.participants.get().status, "removed")

    def test_readd(self):
        self.team_member.states.remove(save=True)
        self.team_member.states.readd(save=True)

        self.assertEqual(self.team_member.status, "active")
        self.assertEqual(self.team_member.participants.get().status, "accepted")
