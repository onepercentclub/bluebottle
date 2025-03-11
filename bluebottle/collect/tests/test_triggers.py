from datetime import timedelta, date

from bluebottle.activities.effects import SetContributionDateEffect
from bluebottle.activities.messages import (
    ActivityExpiredNotification, ActivitySucceededNotification,
    ActivityRejectedNotification, ActivityCancelledNotification,
    ActivityRestoredNotification, InactiveParticipantAddedNotification,
    ParticipantWithdrewConfirmationNotification,
)
from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.collect.effects import CreateCollectContribution
from bluebottle.collect.messages import (
    CollectActivityDateChangedNotification, ParticipantJoinedNotification
)
from bluebottle.collect.states import (
    CollectActivityStateMachine, CollectContributorStateMachine, CollectContributionStateMachine
)
from bluebottle.collect.tests.factories import CollectActivityFactory, CollectContributorFactory
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
            self.assertTransitionEffect(
                CollectContributorStateMachine.succeed,
                participant
            )
            self.assertTransitionEffect(
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
        self.defaults['activity'].states.publish(save=True)

        super().setUp()

    def test_initiate(self):
        self.model = self.factory.build(**self.defaults)
        with self.execute(user=self.model.user):
            self.model.save()
            self.assertEffect(CreateCollectContribution)
            self.assertStatus(self.model, 'accepted')
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
            self.model.save()
            self.assertEffect(CreateCollectContribution)
            self.model.save()
            self.assertTransitionEffect(CollectContributorStateMachine.succeed)
            self.assertStatus(self.model, 'succeeded')
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
            self.model.save()
            self.assertStatus(self.model, 'accepted')
            contribution = self.model.contributions.first()
            self.assertEqual(contribution.start.date(), self.defaults['activity'].start)

    def test_initiate_ended_activity(self):
        self.defaults['activity'].start = date.today() - timedelta(days=10)
        self.defaults['activity'].end = date.today() + timedelta(days=8)
        self.defaults['activity'].save()
        self.model = self.factory.build(**self.defaults)

        with self.execute(user=self.model.user):
            self.model.save()
            self.assertEffect(CreateCollectContribution)
            self.assertTransitionEffect(CollectContributorStateMachine.succeed)
            self.assertStatus(self.model, 'succeeded')
            contribution = self.model.contributions.first()
            self.assertStatus(contribution, 'succeeded')
            self.assertEqual(contribution.start.date(), date.today())

    def test_initiate_other_user(self):
        self.defaults['activity'].start = date.today() - timedelta(days=10)
        self.defaults['activity'].save()
        self.model = self.factory.build(**self.defaults)
        with self.execute(user=BlueBottleUserFactory.create()):
            self.assertEffect(CreateCollectContribution)

            self.assertTransitionEffect(CollectContributorStateMachine.succeed)
            self.model.save()
            contribution = self.model.contributions.first()
            self.assertStatus(contribution, 'succeeded')
            self.assertNotificationEffect(ParticipantAddedNotification)
            self.assertNotificationEffect(ManagerParticipantAddedOwnerNotification)

            self.assertNoNotificationEffect(ParticipantJoinedNotification)
            self.assertNoNotificationEffect(NewParticipantNotification)

    def test_initiate_other_user_inactive(self):
        self.user.is_active = False
        self.user.save()

        self.defaults['activity'].start = date.today() - timedelta(days=10)
        self.defaults['activity'].save()
        self.model = self.factory.build(**self.defaults)
        with self.execute(user=BlueBottleUserFactory.create()):
            self.assertEffect(CreateCollectContribution)

            self.assertTransitionEffect(CollectContributorStateMachine.succeed)
            self.model.save()
            contribution = self.model.contributions.first()
            self.assertStatus(contribution, 'succeeded')
            self.assertNoNotificationEffect(ParticipantAddedNotification)
            self.assertNotificationEffect(InactiveParticipantAddedNotification)
            self.assertNotificationEffect(ManagerParticipantAddedOwnerNotification)

            self.assertNoNotificationEffect(ParticipantJoinedNotification)
            self.assertNoNotificationEffect(NewParticipantNotification)

    def test_initiate_other_owner(self):
        self.defaults['activity'].start = date.today() - timedelta(days=10)
        self.defaults['activity'].end = date.today() + timedelta(days=8)
        self.defaults['activity'].save()
        self.model = self.factory.build(**self.defaults)
        with self.execute(user=self.defaults['activity'].owner):
            self.assertEffect(CreateCollectContribution)

            self.assertTransitionEffect(CollectContributorStateMachine.succeed)
            self.model.save()
            contribution = self.model.contributions.first()
            self.assertStatus(contribution, 'succeeded')
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

    def test_reaccept(self):
        self.create()

        self.model.states.remove(save=True)
        self.model.states.re_accept()
        with self.execute():
            self.assertTransitionEffect(
                CollectContributionStateMachine.succeed, self.model.contributions.first()
            )
            self.assertNotificationEffect(ParticipantAddedNotification)

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
        self.model.activity.start = date.today() - timedelta(days=10)
        self.model.activity.end = date.today() - timedelta(days=5)
        self.model.activity.save()

        self.model.states.remove()

        with self.execute():
            self.assertNoTransitionEffect(CollectActivityStateMachine.expire, self.model.activity)
