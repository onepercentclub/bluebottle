from datetime import timedelta, date
from django.db import connection
import mock
from django.utils import timezone

from bluebottle.clients.utils import LocalTenant
from bluebottle.time_based.tasks import on_a_date_tasks, with_a_deadline_tasks, ongoing_tasks
from bluebottle.time_based.tests.factories import (
    OnADateActivityFactory, WithADeadlineActivityFactory, OngoingActivityFactory,
    ApplicationFactory
)
from bluebottle.initiatives.tests.factories import (
    InitiativeFactory
)
from bluebottle.test.utils import BluebottleTestCase


class TimeBasedActivityPeriodicTasksTestCase():

    def setUp(self):
        super(TimeBasedActivityPeriodicTasksTestCase, self).setUp()
        self.initiative = InitiativeFactory.create(status='approved')
        self.initiative.save()

        self.activity = self.factory.create(initiative=self.initiative, review=False)

        self.activity.states.submit(save=True)

    @property
    def before(self):
        return self.activity.start - timedelta(days=1)

    def test_nothing(self):
        self.assertEqual(self.activity.status, 'open')
        tenant = connection.tenant

        self.run_task(self.before)

        with LocalTenant(tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

    def test_expire(self):
        self.assertEqual(self.activity.status, 'open')
        tenant = connection.tenant

        self.run_task(self.after)

        with LocalTenant(tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'cancelled')

    def test_expire_after_start(self):
        self.assertEqual(self.activity.status, 'open')
        tenant = connection.tenant

        self.run_task(self.during)

        with LocalTenant(tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'cancelled')

    def test_start(self):
        self.assertEqual(self.activity.status, 'open')
        ApplicationFactory.create(activity=self.activity)

        tenant = connection.tenant

        self.run_task(self.during)

        with LocalTenant(tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'running')

    def test_succeed(self):
        self.assertEqual(self.activity.status, 'open')
        ApplicationFactory.create(activity=self.activity)

        tenant = connection.tenant

        self.run_task(self.after)

        with LocalTenant(tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'succeeded')


class OnADateActivityPeriodicTasksTest(TimeBasedActivityPeriodicTasksTestCase, BluebottleTestCase):
    factory = OnADateActivityFactory

    def run_task(self, when):
        with mock.patch.object(timezone, 'now', return_value=when):
            on_a_date_tasks()

    @property
    def during(self):
        return self.activity.start + timedelta(hours=1)

    @property
    def after(self):
        return self.activity.start + self.activity.duration + timedelta(hours=1)


class WithADeadlineActivityPeriodicTasksTest(TimeBasedActivityPeriodicTasksTestCase, BluebottleTestCase):
    factory = WithADeadlineActivityFactory

    def run_task(self, when):
        with mock.patch('bluebottle.time_based.periodic_tasks.date') as mock_date:
            mock_date.today.return_value = when
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            with_a_deadline_tasks()

    @property
    def during(self):
        return self.activity.start

    @property
    def after(self):
        return self.activity.deadline + timedelta(days=1)


class OngoingActivityPeriodicTasksTest(TimeBasedActivityPeriodicTasksTestCase, BluebottleTestCase):
    factory = OngoingActivityFactory

    def run_task(self, when):
        with mock.patch('bluebottle.time_based.periodic_tasks.date') as mock_date:
            mock_date.today.return_value = when
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            ongoing_tasks()

    @property
    def during(self):
        return self.activity.start

    def test_expire(self):
        pass

    def test_succeed(self):
        pass
