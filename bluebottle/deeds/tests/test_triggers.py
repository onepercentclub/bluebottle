from datetime import timedelta, date

from bluebottle.test.utils import TriggerTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from bluebottle.activities.states import OrganizerStateMachine, OrganizerContributionStateMachine
from bluebottle.activities.effects import SetContributionDateEffect

from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.deeds.states import DeedStateMachine
from bluebottle.initiatives.tests.factories import InitiativeFactory


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

    def test_start(self):
        self.defaults['status'] = 'open'
        self.create()

        DeedParticipantFactory.create(activity=self.model)

        self.model.start = date.today() - timedelta(days=1)

        with self.execute():
            self.assertTransitionEffect(DeedStateMachine.start)

    def test_reopen_running(self):
        self.defaults['status'] = 'running'
        self.defaults['start'] = date.today() - timedelta(days=1)
        self.create()

        self.model.start = date.today() + timedelta(days=1)

        with self.execute():
            self.assertTransitionEffect(DeedStateMachine.reopen)

    def test_reopen_expired(self):
        self.defaults['status'] = 'expired'
        self.defaults['start'] = date.today() - timedelta(days=1)
        self.defaults['end'] = date.today() - timedelta(days=1)
        self.create()

        self.model.start = date.today() + timedelta(days=2)
        self.model.end = date.today() + timedelta(days=1)

        with self.execute():
            self.assertTransitionEffect(DeedStateMachine.reopen)

    def test_expire(self):
        self.create()

        self.model.states.submit(save=True)

        self.model.end = date.today() - timedelta(days=1)

        with self.execute():
            self.assertNoTransitionEffect(DeedStateMachine.succeed)
            self.assertTransitionEffect(DeedStateMachine.expire)
            self.assertTransitionEffect(OrganizerStateMachine.fail, self.model.organizer)
            self.assertTransitionEffect(
                OrganizerContributionStateMachine.fail,
                self.model.organizer.contributions.first()
            )

    def test_expire_running(self):
        self.create()

        self.model.states.submit(save=True)

        self.model.start = date.today() - timedelta(days=2)
        self.model.save()
        self.model.end = date.today() - timedelta(days=1)

        with self.execute():
            self.assertNoTransitionEffect(DeedStateMachine.succeed)
            self.assertTransitionEffect(DeedStateMachine.expire)
            self.assertTransitionEffect(OrganizerStateMachine.fail, self.model.organizer)
            self.assertTransitionEffect(
                OrganizerContributionStateMachine.fail,
                self.model.organizer.contributions.first()
            )

    def test_restart_expired(self):
        self.defaults['start'] = date.today() - timedelta(days=2)
        self.defaults['end'] = date.today() - timedelta(days=1)
        self.defaults['status'] = 'expired'

        self.create()

        self.model.end = date.today() + timedelta(days=1)

        with self.execute():
            self.assertTransitionEffect(DeedStateMachine.restart)

    def test_succeed(self):
        self.create()

        self.model.states.submit(save=True)
        DeedParticipantFactory.create(activity=self.model)

        self.model.end = date.today() - timedelta(days=1)

        with self.execute():
            self.assertTransitionEffect(DeedStateMachine.succeed)

    def test_succeed_running(self):
        self.defaults['status'] = 'running'
        self.defaults['start'] = date.today() - timedelta(days=2)

        self.create()
        DeedParticipantFactory.create(activity=self.model)

        self.model.end = date.today() - timedelta(days=1)

        with self.execute():
            self.assertTransitionEffect(DeedStateMachine.succeed)


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

    def test_succeed_accept(self):
        self.defaults['status'] = 'rejected'
        self.create()
        self.model.activity.states.submit(save=True)

        self.model.activity.start = date.today() - timedelta(days=10)
        self.model.activity.end = date.today() - timedelta(days=5)
        self.model.activity.save()

        self.model.states.accept()

        with self.execute():
            self.assertNoTransitionEffect(DeedStateMachine.succeed, self.model.activity)
