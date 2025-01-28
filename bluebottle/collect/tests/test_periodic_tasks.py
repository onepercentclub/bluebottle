from datetime import timedelta, date

import mock
from django.db import connection

from bluebottle.clients.utils import LocalTenant
from bluebottle.collect.tasks import collect_tasks
from bluebottle.collect.tests.factories import CollectActivityFactory, CollectContributorFactory
from bluebottle.initiatives.tests.factories import (
    InitiativeFactory
)
from bluebottle.test.utils import BluebottleTestCase


class CollectPeriodicTasksTestCase(BluebottleTestCase):
    factory = CollectActivityFactory

    def setUp(self):
        super(CollectPeriodicTasksTestCase, self).setUp()
        self.initiative = InitiativeFactory.create(status='approved')

        self.activity = self.factory.create(
            initiative=self.initiative,
            start=date.today() + timedelta(days=10),
            end=date.today() + timedelta(days=20),
        )

        self.activity.states.submit(save=True)

        self.tenant = connection.tenant

    def run_tasks(self, when):
        with mock.patch('bluebottle.collect.periodic_tasks.date') as mock_date:
            mock_date.today.return_value = when
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            collect_tasks()

    def test_nothing(self):
        self.assertEqual(self.activity.status, 'open')

        self.run_tasks(date.today())

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

    def test_start(self):
        self.activity.end = None
        self.activity.save()
        contributors = CollectContributorFactory.create_batch(3, activity=self.activity)
        for contributor in contributors:
            contributor.refresh_from_db()
            self.assertEqual(contributor.status, 'accepted')

        self.run_tasks(self.activity.start + timedelta(days=3))
        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()
            self.assertEqual(self.activity.status, 'open')
            for contributor in contributors:
                contributor.refresh_from_db()
                self.assertEqual(contributor.status, 'succeeded')

    def test_expire(self):
        self.run_tasks(self.activity.start + timedelta(days=1))
        self.run_tasks(self.activity.end + timedelta(days=1))

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'expired')

    def test_expire_no_start(self):
        self.activity.start = None
        self.activity.save()

        self.run_tasks(self.activity.end + timedelta(days=1))

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'expired')

    def test_succeed(self):
        CollectContributorFactory.create(activity=self.activity)

        self.run_tasks(self.activity.start + timedelta(days=1))
        self.run_tasks(self.activity.end + timedelta(days=1))

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'succeeded')

    def test_succeed_same_day(self):
        day = date.today() + timedelta(days=1)
        self.activity.start = day
        self.activity.end = day
        self.activity.save()
        CollectContributorFactory.create(activity=self.activity)

        self.run_tasks(day)
        self.run_tasks(day + timedelta(days=1))

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'succeeded')

    def test_succeed_no_start(self):
        CollectContributorFactory.create(activity=self.activity)

        self.activity.start = None
        self.activity.save()

        self.run_tasks(self.activity.end + timedelta(days=1))

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'succeeded')
