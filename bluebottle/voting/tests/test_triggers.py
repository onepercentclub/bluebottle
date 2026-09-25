from datetime import date, timedelta

from bluebottle.test.utils import TriggerTestCase
from bluebottle.voting.states import PollStateMachine
from bluebottle.voting.tests.factories import PollFactory


class PollTriggersTestCase(TriggerTestCase):
    factory = PollFactory

    def setUp(self):
        super().setUp()
        self.defaults = {
            'status': 'open',
            'end_date': date.today() + timedelta(days=10),
            'title': 'Favourite colour',
        }

    def test_change_deadline_to_past_closes_open_poll(self):
        self.create()
        self.model.end_date = date.today() - timedelta(days=1)

        with self.execute():
            self.assertTransitionEffect(PollStateMachine.close)

        self.model.save()
        self.assertEqual(self.model.status, 'closed')

    def test_change_deadline_to_future_reopens_closed_poll(self):
        self.defaults['status'] = 'closed'
        self.defaults['end_date'] = date.today() - timedelta(days=1)
        self.create()
        self.model.end_date = date.today() + timedelta(days=10)

        with self.execute():
            self.assertTransitionEffect(PollStateMachine.reopen)

        self.model.save()
        self.assertEqual(self.model.status, 'open')

    def test_clear_deadline_reopens_closed_poll(self):
        self.defaults['status'] = 'closed'
        self.defaults['end_date'] = date.today() - timedelta(days=1)
        self.create()
        self.model.end_date = None

        with self.execute():
            self.assertTransitionEffect(PollStateMachine.reopen)

        self.model.save()
        self.assertEqual(self.model.status, 'open')

    def test_change_deadline_does_not_reopen_cancelled_poll(self):
        self.defaults['status'] = 'cancelled'
        self.defaults['end_date'] = date.today() - timedelta(days=1)
        self.create()
        self.model.end_date = date.today() + timedelta(days=10)

        with self.execute():
            self.assertNoTransitionEffect(PollStateMachine.reopen)

        self.model.save()
        self.assertEqual(self.model.status, 'cancelled')

    def test_change_deadline_does_not_close_draft_poll(self):
        self.defaults['status'] = 'draft'
        self.create()
        self.model.end_date = date.today() - timedelta(days=1)

        with self.execute():
            self.assertNoTransitionEffect(PollStateMachine.close)

        self.model.save()
        self.assertEqual(self.model.status, 'draft')

    def test_future_deadline_does_not_close_open_poll(self):
        self.create()
        self.model.end_date = date.today() + timedelta(days=5)

        with self.execute():
            self.assertNoTransitionEffect(PollStateMachine.close)

        self.model.save()
        self.assertEqual(self.model.status, 'open')

    def test_publish_with_past_deadline_closes_poll(self):
        self.defaults['status'] = 'draft'
        self.defaults['end_date'] = date.today() - timedelta(days=1)
        self.create()
        self.model.states.publish()

        with self.execute():
            self.assertTransitionEffect(PollStateMachine.close)

        self.model.save()
        self.assertEqual(self.model.status, 'closed')
