from datetime import timedelta, date

from bluebottle.test.utils import TriggerTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from bluebottle.activities.states import OrganizerStateMachine, EffortContributionStateMachine
from bluebottle.activities.effects import SetContributionDateEffect

from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.deeds.states import DeedStateMachine, DeedParticipantStateMachine
from bluebottle.deeds.effects import RescheduleEffortsEffect, CreateEffortContribution
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

        participant = DeedParticipantFactory.create(activity=self.model)

        self.model.start = date.today() - timedelta(days=1)

        with self.execute():
            self.assertTransitionEffect(DeedStateMachine.start)
            self.assertNoTransitionEffect(
                DeedParticipantStateMachine.succeed,
                participant
            )
            self.assertNoTransitionEffect(
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
            self.assertTransitionEffect(DeedStateMachine.start)

            self.assertTransitionEffect(
                DeedParticipantStateMachine.succeed,
                participant
            )
            self.assertTransitionEffect(
                EffortContributionStateMachine.succeed,
                participant.contributions.first()
            )
            self.assertEffect(RescheduleEffortsEffect)

    def test_reopen_running(self):
        self.defaults['status'] = 'running'
        self.defaults['start'] = date.today() - timedelta(days=1)
        self.create()

        self.model.start = date.today() + timedelta(days=1)

        with self.execute():
            self.assertTransitionEffect(DeedStateMachine.reopen)
            self.assertEffect(RescheduleEffortsEffect)

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
                EffortContributionStateMachine.fail,
                self.model.organizer.contributions.first()
            )
            self.assertEffect(RescheduleEffortsEffect)

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
                EffortContributionStateMachine.fail,
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

    def test_succeed_running(self):
        self.defaults['status'] = 'running'
        self.defaults['start'] = date.today() - timedelta(days=2)

        self.create()
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

    def test_initiate(self):
        self.model = self.factory.build(**self.defaults)
        with self.execute():
            self.assertEffect(CreateEffortContribution)

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

    def test_withdraw(self):
        self.create()

        self.model.states.withdraw()
        with self.execute():
            self.assertTransitionEffect(
                EffortContributionStateMachine.fail, self.model.contributions.first()
            )

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

    def test_reapply_running_no_end(self):
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

    def test_reapply_to_new(self):
        self.create()
        self.model.activity.states.submit(save=True)

        self.model.states.withdraw(save=True)
        self.model.states.reapply()

        with self.execute():
            self.assertEqual(self.effects, [])

    def test_remove(self):
        self.create()

        self.model.states.remove()
        with self.execute():
            self.assertTransitionEffect(
                EffortContributionStateMachine.fail, self.model.contributions.first()
            )

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

    def test_accept_running_no_end(self):
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
        self.defaults['activity'].start = date.today() - timedelta(days=2)
        self.defaults['activity'].end = date.today() - timedelta(days=1)
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
