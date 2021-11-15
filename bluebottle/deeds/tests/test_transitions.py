from datetime import timedelta, date

from bluebottle.test.utils import StateMachineTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory


class DeedStateMachineTestCase(StateMachineTestCase):
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

    def test_draft_complete(self):
        self.create()

        self.assertTransition('submit', self.owner)
        self.assertTransition('submit', self.staff_user)
        self.assertNoTransition('submit', BlueBottleUserFactory.create())

        self.assertTransition('delete', self.owner)
        self.assertTransition('delete', self.staff_user)
        self.assertNoTransition('delete', BlueBottleUserFactory.create())

    def test_draft_incomplete(self):
        self.defaults['title'] = ''
        self.create()

        self.assertTransition('delete', self.owner)

        self.assertNoTransition('submit', self.owner)
        self.assertNoTransition('submit', self.defaults['initiative'].owner)
        self.assertNoTransition('submit', self.defaults['initiative'].activity_manager)
        self.assertNoTransition('submit', self.staff_user)
        self.assertNoTransition('submit', BlueBottleUserFactory.create())

    def test_draft_incomplete_initiative(self):
        self.defaults['initiative'] = InitiativeFactory.create()
        self.create()

        self.assertTransition('delete', self.owner)

        self.assertNoTransition('submit', self.owner)
        self.assertNoTransition('submit', self.staff_user)
        self.assertNoTransition('submit', BlueBottleUserFactory.create())

    def test_open(self):
        self.defaults['status'] = 'open'
        self.create()

        self.assertTransition('cancel', self.owner)
        self.assertTransition('cancel', self.defaults['initiative'].owner)
        self.assertTransition('cancel', self.defaults['initiative'].activity_manager)
        self.assertTransition('cancel', self.staff_user)
        self.assertNoTransition('cancel', BlueBottleUserFactory.create())

        self.assertNoTransition('succeed_manually', self.owner)
        self.assertNoTransition('succeed_manually', self.staff_user)
        self.assertNoTransition('succeed_manually', BlueBottleUserFactory.create())

    def test_open_started_no_end(self):
        self.defaults['status'] = 'open'
        self.defaults['end'] = None
        self.create()
        DeedParticipantFactory.create(activity=self.model)

        self.assertTransition('succeed_manually', self.owner)
        self.assertTransition('succeed_manually', self.defaults['initiative'].owner)
        self.assertTransition('succeed_manually', self.defaults['initiative'].activity_manager)
        self.assertTransition('succeed_manually', self.staff_user)
        self.assertNoTransition('succeed_manually', BlueBottleUserFactory.create())

    def test_open_started_no_end_empty(self):
        self.defaults['status'] = 'open'
        self.defaults['end'] = None
        self.create()

        self.assertNoTransition('succeed_manually', self.owner)
        self.assertNoTransition('succeed_manually', self.defaults['initiative'].owner)
        self.assertNoTransition('succeed_manually', self.defaults['initiative'].activity_manager)
        self.assertNoTransition('succeed_manually', self.staff_user)
        self.assertNoTransition('succeed_manually', BlueBottleUserFactory.create())

    def test_open_started(self):
        self.defaults['status'] = 'open'
        self.create()

        self.assertTransition('cancel', self.owner)
        self.assertTransition('cancel', self.defaults['initiative'].owner)
        self.assertTransition('cancel', self.defaults['initiative'].activity_manager)
        self.assertTransition('cancel', self.staff_user)
        self.assertNoTransition('cancel', BlueBottleUserFactory.create())

        self.assertNoTransition('succeed_manually', self.owner)
        self.assertNoTransition('succeed_manually', self.defaults['initiative'].owner)
        self.assertNoTransition('succeed_manually', self.defaults['initiative'].activity_manager)
        self.assertNoTransition('succeed_manually', self.staff_user)
        self.assertNoTransition('succeed_manually', BlueBottleUserFactory.create())

    def test_open_no_end(self):
        self.defaults['status'] = 'open'
        self.defaults['end'] = None
        self.create()
        DeedParticipantFactory.create(activity=self.model)

        self.assertTransition('succeed_manually', self.owner)
        self.assertTransition('succeed_manually', self.defaults['initiative'].owner)
        self.assertTransition('succeed_manually', self.defaults['initiative'].activity_manager)
        self.assertTransition('succeed_manually', self.staff_user)
        self.assertNoTransition('succeed_manually', BlueBottleUserFactory.create())

    def test_succeeded(self):
        self.defaults['status'] = 'succeeded'
        self.create()

        self.assertTransition('reopen_manually', self.owner)
        self.assertTransition('reopen_manually', self.defaults['initiative'].owner)
        self.assertTransition('reopen_manually', self.defaults['initiative'].activity_manager)
        self.assertTransition('reopen_manually', self.staff_user)
        self.assertNoTransition('reopen_manually', BlueBottleUserFactory.create())

    def test_cancelled(self):
        self.defaults['status'] = 'cancelled'
        self.create()

        self.assertTransition('restore', self.owner)
        self.assertTransition('restore', self.defaults['initiative'].owner)
        self.assertTransition('restore', self.defaults['initiative'].activity_manager)
        self.assertTransition('restore', self.staff_user)
        self.assertNoTransition('restore', BlueBottleUserFactory.create())

    def test_expired(self):
        self.defaults['status'] = 'expired'
        self.create()

        self.assertTransition('reopen_manually', self.owner)
        self.assertTransition('reopen_manually', self.defaults['initiative'].owner)
        self.assertTransition('reopen_manually', self.defaults['initiative'].activity_manager)
        self.assertTransition('reopen_manually', self.staff_user)
        self.assertNoTransition('reopen_manually', BlueBottleUserFactory.create())


class DeedParticipantStateMachineTestCase(StateMachineTestCase):
    factory = DeedParticipantFactory

    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        self.user = BlueBottleUserFactory.create()
        self.staff_user = BlueBottleUserFactory.create(is_staff=True)

        self.defaults = {
            'activity': DeedFactory.create(
                status='open',
                initiative=InitiativeFactory.create(status='approved'),
                owner=self.owner,
                start=date.today() + timedelta(days=10),
                end=date.today() + timedelta(days=20),
            ),
            'user': self.user
        }

        super().setUp()

    def test_new(self):
        self.create()

        self.assertTransition('withdraw', self.user)
        self.assertNoTransition('withdraw', self.staff_user)
        self.assertNoTransition('withdraw', self.owner)

        self.assertNoTransition('remove', self.user)
        self.assertTransition('remove', self.staff_user)
        self.assertTransition('remove', self.owner)

    def test_withdrawn(self):
        self.defaults['status'] = 'withdrawn'
        self.create()

        self.assertTransition('reapply', self.user)
        self.assertNoTransition('reapply', self.staff_user)
        self.assertNoTransition('reapply', self.owner)

    def test_removed(self):
        self.defaults['status'] = 'rejected'
        self.create()

        self.assertNoTransition('accept', self.user)
        self.assertTransition('accept', self.staff_user)
        self.assertTransition('accept', self.owner)
        self.assertTransition('accept', self.defaults['activity'].initiative.owner)
        self.assertTransition('accept', self.defaults['activity'].initiative.activity_manager)
