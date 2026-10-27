from bluebottle.activity_links.tests.factories import LinkedDeedFactory, LinkedFundingFactory
from bluebottle.test.utils import BluebottleTestCase


class LinkedActivityStateMachineTestCase(BluebottleTestCase):
    def setUp(self):
        super(LinkedActivityStateMachineTestCase, self).setUp()
        self.init_projects()

    def test_start_transition_from_new(self):
        linked = LinkedDeedFactory.create(status='new')
        linked.states.start(save=True)
        linked.refresh_from_db()
        self.assertEqual(linked.status, 'open')

    def test_cancel_transition(self):
        linked = LinkedFundingFactory.create(status='open')
        linked.states.cancel(save=True)
        linked.refresh_from_db()
        self.assertEqual(linked.status, 'cancelled')

    def test_succeed_transition(self):
        linked = LinkedFundingFactory.create(status='open')
        linked.states.succeed(save=True)
        linked.refresh_from_db()
        self.assertEqual(linked.status, 'succeeded')
