from datetime import date, timedelta

import mock
from django.db import connection

from bluebottle.clients.utils import LocalTenant
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.voting.tasks import poll_tasks
from bluebottle.voting.tests.factories import PollFactory


class PollPeriodicTasksTestCase(BluebottleTestCase):
    factory = PollFactory

    def setUp(self):
        super().setUp()
        self.poll = self.factory.create(
            status='open',
            end_date=date.today() + timedelta(days=10),
            title='Favourite colour',
        )
        self.tenant = connection.tenant

    def run_tasks(self, when):
        with mock.patch('bluebottle.voting.periodic_tasks.date') as mock_date:
            mock_date.today.return_value = when
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            poll_tasks()

    def test_nothing(self):
        self.assertEqual(self.poll.status, 'open')
        self.run_tasks(date.today())

        with LocalTenant(self.tenant, clear_tenant=True):
            self.poll.refresh_from_db()

        self.assertEqual(self.poll.status, 'open')

    def test_close_when_deadline_passed(self):
        self.run_tasks(self.poll.end_date + timedelta(days=1))

        with LocalTenant(self.tenant, clear_tenant=True):
            self.poll.refresh_from_db()

        self.assertEqual(self.poll.status, 'closed')

    def test_close_on_deadline_day(self):
        self.run_tasks(self.poll.end_date)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.poll.refresh_from_db()

        self.assertEqual(self.poll.status, 'closed')

    def test_no_end_date_stays_open(self):
        self.poll.end_date = None
        self.poll.save()
        self.run_tasks(date.today() + timedelta(days=30))

        with LocalTenant(self.tenant, clear_tenant=True):
            self.poll.refresh_from_db()

        self.assertEqual(self.poll.status, 'open')
