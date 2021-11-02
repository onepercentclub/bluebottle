from datetime import timedelta, date

from bluebottle.activities.messages import ActivityExpiredNotification, ActivitySucceededNotification, \
    ActivityRejectedNotification, ActivityCancelledNotification, ActivityRestoredNotification
from bluebottle.test.utils import TriggerTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.activities.effects import SetContributionDateEffect

from bluebottle.collect.tests.factories import CollectActivityFactory, CollectContributorFactory

from bluebottle.collect.states import (
    CollectActivityStateMachine, CollectContributorStateMachine, CollectContributionStateMachine
)
from bluebottle.collect.effects import CreateCollectContribution, SetOverallContributor
from bluebottle.initiatives.tests.factories import InitiativeFactory


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

    def test_succeed(self):
        self.create()

        self.model.states.submit(save=True)
        CollectContributorFactory.create(activity=self.model)

        self.model.end = date.today() - timedelta(days=1)

        with self.execute():
            self.assertTransitionEffect(CollectActivityStateMachine.succeed)
            self.assertNotificationEffect(ActivitySucceededNotification)

    def test_set_realized(self):
        self.create()

        self.model.realized = 100

        with self.execute():
            self.assertEffect(SetOverallContributor)
            self.model.save()

            self.assertTrue(len(self.model.active_contributors), 1)
            self.assertTrue(self.model.active_contributors.get().value, self.model.realized)
            self.assertTrue(
                self.model.active_contributors.get().contributions.get(), self.model.realized
            )


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
        with self.execute():
            self.assertEffect(CreateCollectContribution)

            self.assertTransitionEffect(CollectContributorStateMachine.succeed)
            self.model.save()
            self.assertTransitionEffect(
                CollectContributionStateMachine.succeed, self.model.contributions.first()
            )

    def test_withdraw(self):
        self.create()

        self.model.states.withdraw()
        with self.execute():
            self.assertTransitionEffect(
                CollectContributionStateMachine.fail, self.model.contributions.first()
            )

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
