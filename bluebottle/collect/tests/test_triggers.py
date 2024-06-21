from datetime import timedelta, date

from bluebottle.activities.effects import SetContributionDateEffect
from bluebottle.activities.messages import (
    ActivityExpiredNotification, ActivitySucceededNotification,
    ActivityRejectedNotification, ActivityCancelledNotification, ActivityRestoredNotification,
    ParticipantWithdrewConfirmationNotification,
)
from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.collect.effects import CreateCollectContribution, SetOverallContributor
from bluebottle.collect.messages import (
    CollectActivityDateChangedNotification, ParticipantJoinedNotification
)
from bluebottle.collect.states import (
    CollectActivityStateMachine, CollectContributorStateMachine, CollectContributionStateMachine
)
from bluebottle.collect.tests.factories import CollectActivityFactory, CollectContributorFactory
from bluebottle.impact.effects import UpdateImpactGoalsForActivityEffect
from bluebottle.impact.tests.factories import ImpactGoalFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import TriggerTestCase
from bluebottle.time_based.messages import (
    ParticipantWithdrewNotification, ParticipantRemovedNotification, ParticipantRemovedOwnerNotification,
    ParticipantAddedNotification, ManagerParticipantAddedOwnerNotification,
    NewParticipantNotification
)


class CollectTriggersTestCase(TriggerTestCase):
    factory = CollectActivityFactory

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
            self.assertTransitionEffect(CollectActivityStateMachine.auto_approve)
            self.assertTransitionEffect(OrganizerStateMachine.succeed, self.model.organizer)
            self.assertEffect(SetContributionDateEffect, self.model.organizer.contributions.first())

    def test_submit_started(self):
        self.defaults['start'] = date.today() - timedelta(days=1)
        self.create()
        self.model.states.submit()

        with self.execute():
            self.assertTransitionEffect(CollectActivityStateMachine.auto_approve)
            self.assertTransitionEffect(OrganizerStateMachine.succeed, self.model.organizer)
            self.assertEffect(SetContributionDateEffect, self.model.organizer.contributions.first())

    def test_submit_finished(self):
        self.defaults['start'] = date.today() - timedelta(days=2)
        self.defaults['end'] = date.today() - timedelta(days=1)
        self.create()
        self.model.states.submit()

        with self.execute():
            self.assertTransitionEffect(CollectActivityStateMachine.auto_approve)
            self.assertTransitionEffect(CollectActivityStateMachine.expire)
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

        participant = CollectContributorFactory.create(activity=self.model)

        self.model.start = date.today() - timedelta(days=1)

        with self.execute():
            self.assertNoTransitionEffect(
                CollectContributorStateMachine.succeed,
                participant
            )
            self.assertNoTransitionEffect(
                CollectContributionStateMachine.succeed,
                participant.contributions.first()
            )

    def test_change_end(self):
        self.defaults['status'] = 'open'
        self.create()

        CollectContributorFactory.create(activity=self.model)

        self.model.end = date.today() + timedelta(days=30)

        with self.execute():
            self.assertNotificationEffect(CollectActivityDateChangedNotification)

    def test_reopen_expired(self):
        self.defaults['status'] = 'expired'
        self.defaults['start'] = date.today() - timedelta(days=1)
        self.defaults['end'] = date.today() - timedelta(days=1)
        self.create()
        CollectContributorFactory.create(activity=self.model)

        self.model.start = date.today() + timedelta(days=2)
        self.model.end = date.today() + timedelta(days=1)

        with self.execute():
            self.assertTransitionEffect(CollectActivityStateMachine.reopen)

    def test_expire(self):
        self.create()

        self.model.states.submit(save=True)
        self.model.end = date.today() - timedelta(days=1)

        with self.execute():
            self.assertNoTransitionEffect(CollectActivityStateMachine.succeed)
            self.assertTransitionEffect(CollectActivityStateMachine.expire)
            self.assertTransitionEffect(OrganizerStateMachine.fail, self.model.organizer)
            self.assertTransitionEffect(
                CollectContributionStateMachine.fail,
                self.model.organizer.contributions.first()
            )
            self.assertNotificationEffect(ActivityExpiredNotification),

    def test_set_end_date(self):
        self.create()

        self.model.states.submit(save=True)
        CollectContributorFactory.create(activity=self.model)

        self.model.end = date.today() - timedelta(days=1)

        with self.execute():
            self.assertTransitionEffect(CollectActivityStateMachine.succeed)
            self.assertNotificationEffect(ActivitySucceededNotification)

    def test_set_realized(self):

        self.defaults['enable_impact'] = True
        self.defaults['target'] = 5

        self.create()
        goal = ImpactGoalFactory.create(activity=self.model, target=10)

        self.model.realized = 100

        with self.execute():
            self.assertEffect(UpdateImpactGoalsForActivityEffect)
            self.assertEffect(SetOverallContributor)

            self.model.save()
            goal.refresh_from_db()

            self.assertEqual(goal.realized_from_contributions, 200)
            self.assertEqual(len(self.model.active_contributors), 1)
            self.assertEqual(self.model.active_contributors.get().value, self.model.realized)
            self.assertEqual(
                self.model.active_contributors.get().contributions.get().value, self.model.realized
            )
            self.assertEqual(
                self.model.active_contributors.get().contributions.get().type, self.model.collect_type
            )

    def test_set_realized_again(self):
        self.test_set_realized()

        self.model.realized = 200

        with self.execute():
            self.assertEffect(SetOverallContributor)
            self.model.save()

            self.assertEqual(len(self.model.active_contributors), 1)
            self.assertEqual(self.model.active_contributors.get().value, self.model.realized)
            self.assertEqual(
                self.model.active_contributors.get().contributions.get().value, self.model.realized
            )

    def test_enable_impact(self):
        self.defaults['target'] = 5
        self.defaults['realized'] = 4

        self.create()
        goal = ImpactGoalFactory.create(activity=self.model, target=10)

        self.model.enable_impact = True

        with self.execute():
            self.assertEffect(UpdateImpactGoalsForActivityEffect)
            self.model.save()
            goal.refresh_from_db()
            self.assertEqual(goal.realized_from_contributions, 8)

    def test_set_target(self):
        self.defaults['enable_impact'] = True
        self.defaults['realized'] = 4

        self.create()
        goal = ImpactGoalFactory.create(activity=self.model, target=10)

        self.model.target = 5

        with self.execute():
            self.assertEffect(UpdateImpactGoalsForActivityEffect)
            self.model.save()
            goal.refresh_from_db()
            self.assertEqual(goal.realized_from_contributions, 8)


class CollectContributorTriggerTestCase(TriggerTestCase):
    factory = CollectContributorFactory

    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        self.staff_user = BlueBottleUserFactory.create(is_staff=True)
        self.user = BlueBottleUserFactory.create()

        self.defaults = {
            'activity': CollectActivityFactory.create(
                initiative=InitiativeFactory.create(status='approved'),
                owner=self.owner,
                start=date.today() + timedelta(days=10),
                end=date.today() + timedelta(days=20),
            ),
            'user': self.user

        }
        self.defaults['activity'].states.submit(save=True)

        super().setUp()

    def test_initiate(self):
        self.model = self.factory.build(**self.defaults)
        with self.execute(user=self.model.user):
            self.assertEffect(CreateCollectContribution)

            self.assertTransitionEffect(CollectContributorStateMachine.succeed)
            self.model.save()
            self.assertTransitionEffect(
                CollectContributionStateMachine.succeed, self.model.contributions.first()
            )
            self.assertNotificationEffect(ParticipantJoinedNotification)
            self.assertNotificationEffect(NewParticipantNotification)

            self.assertNoNotificationEffect(ParticipantAddedNotification)
            self.assertNoNotificationEffect(ParticipantRemovedOwnerNotification)

    def test_initiate_started_activity(self):
        self.defaults['activity'].start = date.today() - timedelta(days=700)
        self.defaults['activity'].end = None
        self.defaults['activity'].save()
        self.model = self.factory.build(**self.defaults)

        with self.execute(user=self.model.user):
            self.assertEffect(CreateCollectContribution)
            self.assertTransitionEffect(CollectContributorStateMachine.succeed)
            self.model.save()
            self.assertTransitionEffect(
                CollectContributionStateMachine.succeed, self.model.contributions.first()
            )
            contribution = self.model.contributions.first()
            self.assertEqual(contribution.start.date(), date.today())

    def test_initiate_future_activity(self):
        self.defaults['activity'].start = date.today() + timedelta(days=700)
        self.defaults['activity'].end = None
        self.defaults['activity'].save()
        self.model = self.factory.build(**self.defaults)

        with self.execute(user=self.model.user):
            self.assertEffect(CreateCollectContribution)
            self.assertTransitionEffect(CollectContributorStateMachine.succeed)
            self.model.save()
            self.assertTransitionEffect(
                CollectContributionStateMachine.succeed, self.model.contributions.first()
            )
            contribution = self.model.contributions.first()
            self.assertEqual(contribution.start.date(), self.defaults['activity'].start)

    def test_initiate_ended_activity(self):
        self.defaults['activity'].start = date.today() - timedelta(days=10)
        self.defaults['activity'].end = date.today() - timedelta(days=8)
        self.defaults['activity'].save()
        self.model = self.factory.build(**self.defaults)

        with self.execute(user=self.model.user):
            self.assertEffect(CreateCollectContribution)
            self.assertTransitionEffect(CollectContributorStateMachine.succeed)
            self.model.save()
            self.assertTransitionEffect(
                CollectContributionStateMachine.succeed, self.model.contributions.first()
            )
            contribution = self.model.contributions.first()
            self.assertEqual(contribution.start.date(), self.defaults['activity'].end)

    def test_initiate_other_user(self):
        self.model = self.factory.build(**self.defaults)
        with self.execute(user=BlueBottleUserFactory.create()):
            self.assertEffect(CreateCollectContribution)

            self.assertTransitionEffect(CollectContributorStateMachine.succeed)
            self.model.save()
            self.assertTransitionEffect(
                CollectContributionStateMachine.succeed, self.model.contributions.first()
            )
            self.assertNotificationEffect(ParticipantAddedNotification)
            self.assertNotificationEffect(ManagerParticipantAddedOwnerNotification)

            self.assertNoNotificationEffect(ParticipantJoinedNotification)
            self.assertNoNotificationEffect(NewParticipantNotification)

    def test_initiate_other_owner(self):
        self.model = self.factory.build(**self.defaults)
        with self.execute(user=self.defaults['activity'].owner):
            self.assertEffect(CreateCollectContribution)

            self.assertTransitionEffect(CollectContributorStateMachine.succeed)
            self.model.save()
            self.assertTransitionEffect(
                CollectContributionStateMachine.succeed, self.model.contributions.first()
            )
            self.assertNotificationEffect(ParticipantAddedNotification)
            self.assertNoNotificationEffect(ManagerParticipantAddedOwnerNotification)

    def test_withdraw(self):
        self.create()

        self.model.states.withdraw()
        with self.execute():
            self.assertTransitionEffect(
                CollectContributionStateMachine.fail, self.model.contributions.first()
            )
            self.assertNotificationEffect(ParticipantWithdrewNotification)
            self.assertNotificationEffect(ParticipantWithdrewConfirmationNotification)

    def test_reapply(self):
        self.create()

        self.model.states.withdraw(save=True)
        self.model.states.reapply()

        with self.execute():
            self.assertTransitionEffect(
                CollectContributionStateMachine.succeed, self.model.contributions.first()
            )

            self.assertTransitionEffect(
                CollectContributorStateMachine.succeed
            )
            self.assertNotificationEffect(ParticipantJoinedNotification)

    def test_reapply_finished(self):
        self.defaults['activity'].end = date.today() - timedelta(days=2)
        self.defaults['activity'].save()

        self.create()

        self.model.states.withdraw(save=True)
        self.model.states.reapply()

        with self.execute():
            self.assertTransitionEffect(
                CollectContributionStateMachine.succeed, self.model.contributions.first()
            )

            self.assertTransitionEffect(
                CollectActivityStateMachine.succeed, self.model.activity
            )

            self.assertTransitionEffect(
                CollectContributorStateMachine.succeed
            )

    def test_remove(self):
        self.create()

        self.model.states.remove()
        with self.execute():
            self.assertTransitionEffect(
                CollectContributionStateMachine.fail, self.model.contributions.first()
            )
            self.assertNotificationEffect(ParticipantRemovedNotification)
            self.assertNotificationEffect(ParticipantRemovedOwnerNotification)

    def test_remove_finished(self):
        self.create()

        self.model.activity.end = date.today() - timedelta(days=5)
        self.model.activity.save()

        self.model.states.remove()

        with self.execute():
            self.assertTransitionEffect(CollectActivityStateMachine.expire, self.model.activity)

    def test_not_expire_remove_one_left(self):
        self.create()

        CollectContributorFactory.create(activity=self.model.activity)

        self.model.activity.end = date.today() - timedelta(days=5)
        self.model.activity.save()

        self.model.states.remove()

        with self.execute():
            self.assertNoTransitionEffect(CollectActivityStateMachine.expire, self.model.activity)
