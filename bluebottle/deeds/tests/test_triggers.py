import uuid
from datetime import timedelta, date

from bluebottle.activities.effects import CreateTeamEffect, CreateInviteEffect
from bluebottle.activities.effects import SetContributionDateEffect
from bluebottle.activities.messages import (
    ActivityExpiredNotification, ActivitySucceededNotification,
    ActivityRejectedNotification, ActivityCancelledNotification, ActivityRestoredNotification,
    ParticipantWithdrewConfirmationNotification, TeamMemberAddedMessage, TeamMemberWithdrewMessage,
    TeamMemberRemovedMessage
)
from bluebottle.activities.models import Activity
from bluebottle.activities.states import OrganizerStateMachine, EffortContributionStateMachine
from bluebottle.deeds.effects import RescheduleEffortsEffect, CreateEffortContribution, SetEndDateEffect
from bluebottle.deeds.messages import (
    DeedDateChangedNotification, ParticipantJoinedNotification
)
from bluebottle.deeds.states import DeedStateMachine, DeedParticipantStateMachine
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory, EffortContributionFactory
from bluebottle.impact.effects import UpdateImpactGoalEffect
from bluebottle.impact.effects import UpdateImpactGoalsForActivityEffect
from bluebottle.impact.tests.factories import ImpactGoalFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import TriggerTestCase
from bluebottle.time_based.messages import (
    TeamParticipantRemovedNotification, ParticipantRemovedNotification, NewParticipantNotification,
    ParticipantAddedNotification, ParticipantAddedOwnerNotification, ParticipantWithdrewNotification
)


class DeedTriggersTestCase(TriggerTestCase):
    factory = DeedFactory

    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        self.staff_user = BlueBottleUserFactory.create(is_staff=True)

        self.defaults = {
            'initiative': InitiativeFactory.create(status='approved'),
            'owner': self.owner,
            'start': date.today() + timedelta(days=10),
            'end': date.today() + timedelta(days=20),
        }
        super().setUp()

    def test_submit(self):
        self.create()
        self.model.states.submit()

        with self.execute():
            self.assertTransitionEffect(DeedStateMachine.auto_approve)
            self.assertTransitionEffect(OrganizerStateMachine.succeed, self.model.organizer)
            self.assertEffect(SetContributionDateEffect, self.model.organizer.contributions.first())

    def test_started(self):
        self.defaults['start'] = date.today() - timedelta(days=1)
        self.create()
        self.model.states.submit()

        with self.execute():
            self.assertTransitionEffect(DeedStateMachine.auto_approve)
            self.assertTransitionEffect(OrganizerStateMachine.succeed, self.model.organizer)
            self.assertEffect(SetContributionDateEffect, self.model.organizer.contributions.first())

    def test_finished(self):
        self.defaults['start'] = date.today() - timedelta(days=2)
        self.defaults['end'] = date.today() - timedelta(days=1)
        self.create()
        self.model.states.submit()

        with self.execute():
            self.assertTransitionEffect(DeedStateMachine.auto_approve)
            self.assertTransitionEffect(DeedStateMachine.expire)
            self.assertTransitionEffect(OrganizerStateMachine.succeed, self.model.organizer)
            self.assertEffect(SetContributionDateEffect, self.model.organizer.contributions.first())

    def test_reject(self):
        self.create()
        self.model.states.submit(save=True)
        self.model.states.reject()

        with self.execute():
            self.assertTransitionEffect(OrganizerStateMachine.fail, self.model.organizer)
            self.assertNotificationEffect(ActivityRejectedNotification)

    def test_cancel(self):
        self.create()
        self.model.states.submit(save=True)
        self.model.states.cancel()

        with self.execute():
            self.assertTransitionEffect(OrganizerStateMachine.fail, self.model.organizer)
            self.assertNotificationEffect(ActivityCancelledNotification)

    def test_restored(self):
        self.create()
        self.model.states.reject(save=True)
        self.model.states.restore()

        with self.execute():
            self.assertTransitionEffect(OrganizerStateMachine.reset, self.model.organizer)
            self.assertNotificationEffect(ActivityRestoredNotification)

    def test_start(self):
        self.defaults['status'] = 'open'
        self.create()

        participant = DeedParticipantFactory.create(activity=self.model)

        self.model.start = date.today() - timedelta(days=1)

        with self.execute():
            self.assertTransitionEffect(
                DeedParticipantStateMachine.succeed,
                participant
            )
            self.assertTransitionEffect(
                EffortContributionStateMachine.succeed,
                participant.contributions.first()
            )
            self.assertEffect(RescheduleEffortsEffect)

    def test_start_no_end(self):
        self.defaults['status'] = 'open'
        self.defaults['end'] = None
        self.create()

        participant = DeedParticipantFactory.create(activity=self.model)

        self.model.start = date.today() - timedelta(days=1)

        with self.execute():
            self.assertTransitionEffect(
                DeedParticipantStateMachine.succeed,
                participant
            )
            self.assertTransitionEffect(
                EffortContributionStateMachine.succeed,
                participant.contributions.first()
            )
            self.assertEffect(RescheduleEffortsEffect)

    def test_reopen_expired(self):
        self.defaults['status'] = 'expired'
        self.defaults['start'] = date.today() - timedelta(days=1)
        self.defaults['end'] = date.today() - timedelta(days=1)
        self.create()
        DeedParticipantFactory.create(activity=self.model)

        self.model.start = date.today() + timedelta(days=2)
        self.model.end = date.today() + timedelta(days=1)

        with self.execute():
            self.assertTransitionEffect(DeedStateMachine.reopen)
            self.assertNotificationEffect(DeedDateChangedNotification)

    def test_restart_expired(self):
        self.defaults['status'] = 'expired'
        self.defaults['start'] = date.today() - timedelta(days=1)
        self.defaults['end'] = date.today() - timedelta(days=1)
        self.create()
        DeedParticipantFactory.create(activity=self.model)

        self.model.end = date.today() + timedelta(days=1)

        with self.execute():
            self.assertNotificationEffect(DeedDateChangedNotification)

    def test_reschedule_open(self):
        self.defaults['status'] = 'open'
        self.defaults['start'] = date.today() + timedelta(days=1)
        self.defaults['end'] = date.today() + timedelta(days=3)
        self.create()
        DeedParticipantFactory.create(activity=self.model)

        self.model.start = date.today() + timedelta(days=2)

        with self.execute():
            self.assertNotificationEffect(DeedDateChangedNotification)

    def test_expire(self):
        self.create()

        self.model.states.submit(save=True)
        self.model.end = date.today() - timedelta(days=1)

        with self.execute():
            self.assertNoTransitionEffect(DeedStateMachine.succeed)
            self.assertTransitionEffect(DeedStateMachine.expire)
            self.assertTransitionEffect(OrganizerStateMachine.fail, self.model.organizer)
            self.assertTransitionEffect(
                EffortContributionStateMachine.fail,
                self.model.organizer.contributions.first()
            )
            self.assertNotificationEffect(ActivityExpiredNotification),
            self.assertEffect(RescheduleEffortsEffect)

    def test_set_end_date(self):
        self.create()

        self.model.states.submit(save=True)
        participant = DeedParticipantFactory.create(activity=self.model)

        self.model.end = date.today() - timedelta(days=1)

        with self.execute():
            self.assertTransitionEffect(DeedStateMachine.succeed)
            self.assertTransitionEffect(
                DeedParticipantStateMachine.succeed,
                participant
            )
            self.assertTransitionEffect(
                EffortContributionStateMachine.succeed,
                participant.contributions.first()
            )
            self.assertNotificationEffect(ActivitySucceededNotification)

    def test_succeed(self):
        self.create()

        self.model.states.submit(save=True)
        participant = DeedParticipantFactory.create(activity=self.model)

        self.model.states.succeed()

        with self.execute():
            self.assertTransitionEffect(
                DeedParticipantStateMachine.succeed,
                participant
            )
            self.assertTransitionEffect(
                EffortContributionStateMachine.succeed,
                participant.contributions.first()
            )
            self.assertEffect(SetEndDateEffect)

    def test_restart_succeeded(self):
        self.defaults['status'] = 'succeeded'
        self.defaults['start'] = date.today() - timedelta(days=2)
        self.defaults['end'] = date.today() - timedelta(days=1)

        self.create()
        participant = DeedParticipantFactory.create(activity=self.model)

        self.model.end = date.today() + timedelta(days=1)

        with self.execute():
            self.assertTransitionEffect(DeedStateMachine.reopen)
            self.assertTransitionEffect(
                DeedParticipantStateMachine.re_accept,
                participant
            )
            self.assertTransitionEffect(
                EffortContributionStateMachine.reset,
                participant.contributions.first()
            )

    def test_enable_impact(self):
        self.defaults['status'] = 'open'
        self.defaults['target'] = 5

        self.create()
        goal = ImpactGoalFactory.create(activity=self.model, target=10)
        DeedParticipantFactory.create(activity=self.model)

        self.model.enable_impact = True

        with self.execute():
            self.assertEffect(UpdateImpactGoalsForActivityEffect)
            self.model.save()
            goal.refresh_from_db()
            self.assertEqual(goal.realized_from_contributions, 2)

    def test_disable_impact(self):
        self.defaults['status'] = 'open'
        self.defaults['target'] = 5
        self.defaults['enable_impact'] = True

        self.create()
        goal = ImpactGoalFactory.create(activity=self.model, target=10)
        DeedParticipantFactory.create(activity=self.model)

        self.model.enable_impact = False

        with self.execute():
            self.assertEffect(UpdateImpactGoalsForActivityEffect)
            self.model.save()
            goal.refresh_from_db()

            self.assertEqual(goal.realized_from_contributions, None)

    def test_change_target(self):
        self.defaults['status'] = 'open'
        self.defaults['target'] = 5
        self.defaults['enable_impact'] = True

        self.create()
        goal = ImpactGoalFactory.create(activity=self.model, target=10)
        DeedParticipantFactory.create(activity=self.model)

        self.model.target = 4

        with self.execute():
            self.assertEffect(UpdateImpactGoalsForActivityEffect)
            self.model.save()
            goal.refresh_from_db()

            self.assertEqual(goal.realized_from_contributions, 2.5)


class DeedParticipantTriggersTestCase(TriggerTestCase):
    factory = DeedParticipantFactory

    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        self.staff_user = BlueBottleUserFactory.create(is_staff=True)
        self.user = BlueBottleUserFactory.create()

        self.defaults = {
            'activity': DeedFactory.create(
                initiative=InitiativeFactory.create(status='approved'),
                owner=self.owner,
                start=date.today() + timedelta(days=10),
                end=date.today() + timedelta(days=20),
            ),
            'user': self.user

        }
        super().setUp()

    def test_initiate_future_start(self):
        self.model = self.factory.build(**self.defaults)
        with self.execute(user=self.user):
            self.assertEffect(CreateEffortContribution)
            self.assertNotificationEffect(NewParticipantNotification)
            self.assertNotificationEffect(ParticipantJoinedNotification)
            self.assertEffect(CreateInviteEffect)
            self.model.save()
            self.assertEqual(
                self.model.status,
                'accepted'
            )
            self.assertEqual(
                self.model.contributions.first().status,
                'new'
            )
            self.assertTrue(isinstance(self.model.invite.pk, uuid.UUID))

    def test_initiate_passed_start(self):
        self.defaults['activity'].start = date.today() - timedelta(days=2)
        self.defaults['activity'].end = None
        self.defaults['activity'].save()
        self.model = self.factory.build(**self.defaults)
        with self.execute(user=self.user):
            self.assertEffect(CreateEffortContribution)
            self.assertNotificationEffect(NewParticipantNotification)
            self.assertNotificationEffect(ParticipantJoinedNotification)
            self.model.save()
            self.assertTransitionEffect(
                EffortContributionStateMachine.succeed, self.model.contributions.first()
            )
            contribution = self.model.contributions.first()
            self.assertEqual(contribution.start.date(), date.today())

    def test_initiate_team(self):
        self.defaults['activity'].team_activity = Activity.TeamActivityChoices.teams
        self.model = self.factory.build(**self.defaults)
        with self.execute(user=self.user):
            self.assertEffect(CreateTeamEffect)
            self.assertNoNotificationEffect(TeamMemberAddedMessage)

        self.model.save()
        self.assertTrue(self.model.team.id)
        self.assertEqual(self.model.team.owner, self.model.user)

    def test_initiate_by_invite(self):
        self.defaults['activity'].team_activity = Activity.TeamActivityChoices.teams
        team_captain = self.factory.create(**self.defaults)

        self.defaults['user'] = BlueBottleUserFactory.create()
        self.defaults['accepted_invite'] = team_captain.invite

        self.model = self.factory.build(**self.defaults)
        with self.execute(user=self.user):
            self.assertEffect(CreateTeamEffect)
            self.assertNotificationEffect(TeamMemberAddedMessage, [team_captain.user])

        self.model.save()
        self.assertEqual(self.model.team, team_captain.team)
        self.assertEqual(self.model.team.owner, team_captain.user)

    def test_initiate_individual(self):
        self.defaults['activity'].team_activity = Activity.TeamActivityChoices.individuals
        self.model = self.factory.build(**self.defaults)
        with self.execute(user=self.user):
            self.assertNoEffect(CreateTeamEffect)

    def test_added_by_admin(self):
        self.model = self.factory.build(**self.defaults)
        with self.execute(user=self.staff_user):
            self.assertEffect(CreateEffortContribution)
            self.assertNotificationEffect(ParticipantAddedNotification)
            self.assertNotificationEffect(ParticipantAddedOwnerNotification)

    def test_initiate_no_start_no_end(self):
        self.defaults['activity'].start = None
        self.defaults['activity'].end = None
        self.defaults['activity'].save()

        self.model = self.factory.build(**self.defaults)
        with self.execute():
            effect = self.assertEffect(CreateEffortContribution)
            self.assertEqual(effect.contribution.contribution_type, 'deed')

            self.assertTransitionEffect(DeedParticipantStateMachine.succeed)
            self.model.save()
            self.assertTransitionEffect(
                EffortContributionStateMachine.succeed, self.model.contributions.first()
            )

    def test_initiate_succeeded(self):
        self.defaults['activity'].start = date.today() - timedelta(days=2)
        self.defaults['activity'].end = date.today() - timedelta(days=1)
        self.defaults['activity'].save()

        self.model = self.factory.build(**self.defaults)

        with self.execute():
            effect = self.assertEffect(CreateEffortContribution)
            self.assertEqual(effect.contribution.contribution_type, 'deed')

            self.assertTransitionEffect(DeedParticipantStateMachine.succeed)
            self.model.save()
            self.assertTransitionEffect(
                EffortContributionStateMachine.succeed, self.model.contributions.first()
            )

    def test_initiate_started(self):
        self.defaults['activity'].start = None
        self.defaults['activity'].end = date.today() + timedelta(days=1)
        self.defaults['activity'].save()

        self.model = self.factory.build(**self.defaults)

        with self.execute():
            effect = self.assertEffect(CreateEffortContribution)
            self.assertEqual(effect.contribution.contribution_type, 'deed')

            self.assertTransitionEffect(DeedParticipantStateMachine.succeed)
            self.model.save()
            self.assertTransitionEffect(
                EffortContributionStateMachine.succeed, self.model.contributions.first()
            )

    def test_withdraw(self):
        self.create()

        self.model.states.withdraw()
        with self.execute():
            self.assertTransitionEffect(
                EffortContributionStateMachine.fail, self.model.contributions.first()
            )

            self.assertNotificationEffect(ParticipantWithdrewNotification)
            self.assertNotificationEffect(ParticipantWithdrewConfirmationNotification)
            self.assertNoNotificationEffect(TeamMemberWithdrewMessage)

    def test_withdraw_team(self):
        self.defaults['activity'].team_activity = Activity.TeamActivityChoices.teams
        team_captain = self.factory.create(**self.defaults)

        self.defaults['user'] = BlueBottleUserFactory.create()
        self.defaults['accepted_invite'] = team_captain.invite

        self.create()

        self.model.states.withdraw()
        with self.execute():
            self.assertNotificationEffect(TeamMemberWithdrewMessage)

    def test_reapply_no_start_no_end(self):
        self.defaults['activity'].start = None
        self.defaults['activity'].end = None
        self.defaults['activity'].save()

        self.create()
        self.model.activity.states.submit(save=True)

        self.model.states.withdraw(save=True)
        self.model.states.reapply()

        with self.execute():
            self.assertTransitionEffect(
                EffortContributionStateMachine.succeed, self.model.contributions.first()
            )

            self.assertTransitionEffect(
                DeedParticipantStateMachine.succeed
            )

    def test_reapply_started(self):
        self.defaults['activity'].start = date.today() - timedelta(days=2)
        self.defaults['activity'].end = None
        self.defaults['activity'].states.submit(save=True)

        self.create()

        self.model.states.withdraw(save=True)
        self.model.states.reapply()

        with self.execute():
            self.assertTransitionEffect(
                EffortContributionStateMachine.succeed, self.model.contributions.first()
            )

            self.assertTransitionEffect(
                DeedParticipantStateMachine.succeed
            )

    def test_reapply_cancelled_team(self):
        self.defaults['activity'].team_activity = Activity.TeamActivityChoices.teams

        self.defaults['activity'].start = date.today() - timedelta(days=2)
        self.defaults['activity'].end = None
        self.defaults['activity'].states.submit(save=True)

        self.create()

        self.assertEqual(self.model.contributions.first().status, 'succeeded')
        self.assertEqual(self.model.status, 'succeeded')

        self.model.states.withdraw(save=True)
        self.model.team.states.cancel(save=True)
        self.model.states.reapply()

        with self.execute():
            self.assertNoTransitionEffect(
                EffortContributionStateMachine.succeed, self.model.contributions.first()
            )

            self.assertNoTransitionEffect(
                DeedParticipantStateMachine.succeed
            )

        self.model.save()
        self.model.team.states.reopen(save=True)

        self.model.refresh_from_db()
        self.assertEqual(self.model.status, 'succeeded')
        self.assertEqual(self.model.contributions.first().status, 'succeeded')

    def test_reapply_to_new(self):
        self.create()
        self.model.activity.states.submit(save=True)

        self.model.states.withdraw(save=True)
        self.model.states.reapply()

        with self.execute():
            self.assertTransitionEffect(
                EffortContributionStateMachine.reset,
                self.model.contributions.first()
            )

    def test_remove(self):
        self.create()

        self.model.states.remove()
        with self.execute():
            self.assertTransitionEffect(
                EffortContributionStateMachine.fail, self.model.contributions.first()
            )
            self.assertNotificationEffect(ParticipantRemovedNotification)

    def test_remove_team(self):
        self.defaults['activity'].team_activity = Activity.TeamActivityChoices.teams
        team_captain = self.factory.create(**self.defaults)

        self.defaults['user'] = BlueBottleUserFactory.create()
        self.defaults['accepted_invite'] = team_captain.invite

        self.create()

        self.model.states.remove()
        with self.execute():
            self.assertTransitionEffect(
                EffortContributionStateMachine.fail, self.model.contributions.first()
            )
            self.assertNotificationEffect(TeamParticipantRemovedNotification)
            self.assertNotificationEffect(TeamMemberRemovedMessage)

    def test_expire_remove(self):
        self.create()
        self.model.activity.states.submit(save=True)

        self.model.activity.start = date.today() - timedelta(days=10)
        self.model.activity.end = date.today() - timedelta(days=5)
        self.model.activity.save()

        self.model.states.remove()

        with self.execute():
            self.assertTransitionEffect(DeedStateMachine.expire, self.model.activity)

    def test_not_expire_remove_one_left(self):
        self.create()
        self.model.activity.states.submit(save=True)

        DeedParticipantFactory.create(activity=self.model.activity)

        self.model.activity.start = date.today() - timedelta(days=10)
        self.model.activity.end = date.today() - timedelta(days=5)
        self.model.activity.save()

        self.model.states.remove()

        with self.execute():
            self.assertNoTransitionEffect(DeedStateMachine.expire, self.model.activity)

    def test_accept_no_start_no_end(self):
        self.defaults['activity'].start = None
        self.defaults['activity'].end = None
        self.defaults['activity'].save()

        self.create()
        self.model.activity.states.submit(save=True)

        self.model.states.remove(save=True)
        self.model.states.accept()

        with self.execute():
            self.assertTransitionEffect(
                EffortContributionStateMachine.succeed, self.model.contributions.first()
            )

            self.assertTransitionEffect(
                DeedParticipantStateMachine.succeed
            )

    def test_accept_started_no_end(self):
        self.defaults['activity'].start = date.today() - timedelta(days=2)
        self.defaults['activity'].end = None
        self.defaults['activity'].states.submit(save=True)

        self.create()

        self.model.states.remove(save=True)
        self.model.states.accept()

        with self.execute():
            self.assertTransitionEffect(
                EffortContributionStateMachine.succeed, self.model.contributions.first()
            )

            self.assertTransitionEffect(
                DeedParticipantStateMachine.succeed
            )

    def test_accept_expired(self):
        self.defaults['activity'].start = date.today() - timedelta(days=20)
        self.defaults['activity'].end = date.today() - timedelta(days=10)
        self.defaults['activity'].status = 'expired'
        self.defaults['activity'].save()

        self.create()

        self.model.states.remove(save=True)
        self.model.states.accept()

        with self.execute():
            self.assertTransitionEffect(
                DeedParticipantStateMachine.succeed
            )
            self.assertTransitionEffect(
                EffortContributionStateMachine.succeed, self.model.contributions.first()
            )
            self.assertTransitionEffect(
                DeedStateMachine.succeed, self.model.activity
            )

    def test_succeed_accept(self):
        self.defaults['status'] = 'rejected'
        activity = DeedFactory.create(
            status='expired',
            initiative=InitiativeFactory.create(status='approved'),
            start=date.today() - timedelta(days=10),
            end=date.today() - timedelta(days=2),
        )
        self.defaults['activity'] = activity
        self.create()
        self.model.activity.save()
        self.model.states.accept()

        with self.execute():
            self.assertTransitionEffect(DeedStateMachine.succeed, self.model.activity)


class EffortContributionTriggersTestCase(TriggerTestCase):
    factory = EffortContributionFactory

    def setUp(self):
        self.defaults = {
            'contributor': DeedParticipantFactory(
                activity=DeedFactory(enable_impact=True)
            )
        }

        self.impact_goal = ImpactGoalFactory.create(
            activity=self.defaults['contributor'].activity,
            target=100
        )

    def test_succeed_update_impact(self):
        self.create()
        self.model.states.succeed()
        with self.execute():
            self.assertEffect(UpdateImpactGoalEffect, self.model)

    def test_fail_update_impact(self):
        self.create()
        self.model.states.fail()
        with self.execute():
            self.assertEffect(UpdateImpactGoalEffect, self.model)
