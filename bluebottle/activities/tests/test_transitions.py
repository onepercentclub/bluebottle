from bluebottle.test.utils import StateMachineTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from bluebottle.time_based.tests.factories import PeriodActivityFactory
from bluebottle.activities.tests.factories import TeamFactory


class DeedStateMachineTestCase(StateMachineTestCase):
    factory = TeamFactory

    def setUp(self):
        self.activity_owner = BlueBottleUserFactory.create()
        self.team_captain = BlueBottleUserFactory.create()
        self.staff_user = BlueBottleUserFactory.create(is_staff=True)

        self.defaults = {
            'activity': PeriodActivityFactory.create(
                status='open', owner=self.activity_owner, review=False
            ),
            'owner': self.team_captain,
        }
        super().setUp()

    def test_open(self):
        self.create()

        self.assertTransition('withdraw', self.team_captain)
        self.assertNoTransition('withdraw', self.staff_user)
        self.assertNoTransition('withdraw', self.activity_owner)
        self.assertNoTransition('withdraw', BlueBottleUserFactory.create())

        self.assertNoTransition('cancel', self.team_captain)
        self.assertTransition('cancel', self.staff_user)
        self.assertTransition('cancel', self.activity_owner)
        self.assertNoTransition('cancel', BlueBottleUserFactory.create())

    def test_withdrawn(self):
        self.defaults['status'] = 'withdrawn'
        self.create()

        self.assertTransition('reapply', self.team_captain)
        self.assertNoTransition('reapply', self.staff_user)
        self.assertNoTransition('reapply', self.activity_owner)
        self.assertNoTransition('reapply', BlueBottleUserFactory.create())

    def test_rejected(self):
        self.defaults['status'] = 'cancelled'
        self.create()

        self.assertNoTransition('reopen', self.team_captain)
        self.assertTransition('reopen', self.staff_user)
        self.assertTransition('reopen', self.activity_owner)
        self.assertNoTransition('reopen', BlueBottleUserFactory.create())
