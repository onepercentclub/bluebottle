from datetime import timedelta, date, datetime
from django.db import connection
import mock
from django.utils import timezone

from bluebottle.clients.utils import LocalTenant
from bluebottle.time_based.tasks import (
    on_a_date_tasks, with_a_deadline_tasks, ongoing_tasks,
    period_application_tasks, duration_tasks
)
from bluebottle.time_based.tests.factories import (
    OnADateActivityFactory, WithADeadlineActivityFactory, OngoingActivityFactory,
    OnADateApplicationFactory, PeriodApplicationFactory
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
        self.tenant = connection.tenant

    @property
    def before(self):
        return self.activity.start - timedelta(days=1)

    def test_nothing(self):
        self.assertEqual(self.activity.status, 'open')

        self.run_task(self.before)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

    def test_expire(self):
        self.assertEqual(self.activity.status, 'open')

        self.run_task(self.after)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'cancelled')

    def test_expire_after_start(self):
        self.assertEqual(self.activity.status, 'open')

        self.run_task(self.during)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'cancelled')

    def test_start(self):
        self.assertEqual(self.activity.status, 'open')
        self.application_factory.create(activity=self.activity)

        self.run_task(self.during)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'running')

    def test_succeed(self):
        self.assertEqual(self.activity.status, 'open')
        self.application_factory.create(activity=self.activity)

        self.run_task(self.after)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'succeeded')


class OnADateActivityPeriodicTasksTest(TimeBasedActivityPeriodicTasksTestCase, BluebottleTestCase):
    factory = OnADateActivityFactory
    application_factory = OnADateApplicationFactory

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
    application_factory = PeriodApplicationFactory

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
    application_factory = PeriodApplicationFactory

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


class WithADeadlineApplicationPeriodicTest(BluebottleTestCase):
    factory = WithADeadlineActivityFactory
    application_factory = PeriodApplicationFactory

    def setUp(self):
        super().setUp()
        self.initiative = InitiativeFactory.create(status='approved')
        self.initiative.save()

        self.activity = self.factory.create(
            initiative=self.initiative,
            review=False,
            duration=timedelta(hours=2),
            duration_period='weeks'
        )
        self.activity.states.submit(save=True)
        self.application = self.application_factory.create(activity=self.activity)

    def refresh(self):
        with LocalTenant(self.tenant, clear_tenant=True):
            self.application.refresh_from_db()
            self.activity.refresh_from_db()

    def run_tasks(self, when):
        with mock.patch('bluebottle.time_based.periodic_tasks.date') as mock_date:
            mock_date.today.return_value = when
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            with mock.patch('bluebottle.time_based.triggers.date') as mock_date:
                mock_date.today.return_value = when
                mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

                with mock.patch.object(
                    timezone, 'now',
                    return_value=timezone.get_current_timezone().localize(
                        datetime(when.year, when.month, when.day)
                    )
                ):
                    with_a_deadline_tasks()
                    period_application_tasks()
                    duration_tasks()

    def test_contribution_value_is_created(self):
        self.run_tasks(self.activity.start)
        self.refresh()

        self.assertEqual(
            self.application.contribution_values.get().status,
            'new'
        )

    def test_contribution_value_is_succeeded(self):
        self.run_tasks(self.activity.start)
        self.run_tasks(self.activity.start + timedelta(weeks=1, days=1))
        self.refresh()

        self.assertEqual(
            len(self.application.contribution_values.filter(status='succeeded')),
            1
        )

        self.assertEqual(
            len(self.application.contribution_values.filter(status='new')),
            1
        )

    def test_running_time(self):
        days = (self.activity.deadline - self.activity.start).days + 2

        for day in range(days):
            self.run_tasks(self.activity.start + timedelta(days=day))
            self.refresh()

        self.assertEqual(
            len(self.application.contribution_values.all()), 4
        )

        self.assertEqual(
            len(self.application.contribution_values.filter(status='succeeded')),
            3
        )

        self.assertEqual(
            len(self.application.contribution_values.filter(status='new')),
            1
        )

    def test_cancel(self):
        days = (self.activity.deadline - self.activity.start).days + 2

        for day in range(days):
            self.run_tasks(self.activity.start + timedelta(days=day))
            self.refresh()

        self.assertEqual(
            len(self.application.contribution_values.all()), 4
        )
        self.activity.states.cancel(save=True)

        for contribution in self.application.contribution_values.all():
            self.assertEqual(contribution.status, 'failed')


class WithADeadlineReviewApplicationPeriodicTest(BluebottleTestCase):
    factory = WithADeadlineActivityFactory
    application_factory = PeriodApplicationFactory

    def setUp(self):
        super().setUp()
        self.initiative = InitiativeFactory.create(status='approved')
        self.initiative.save()

        self.activity = self.factory.create(
            initiative=self.initiative,
            review=True,
            duration=timedelta(hours=2),
            duration_period='weeks'
        )
        self.activity.states.submit(save=True)
        self.application = self.application_factory.create(activity=self.activity)

    def refresh(self):
        with LocalTenant(self.tenant, clear_tenant=True):
            self.application.refresh_from_db()
            self.activity.refresh_from_db()

    def run_tasks(self, when):
        with mock.patch('bluebottle.time_based.periodic_tasks.date') as mock_date:
            mock_date.today.return_value = when
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            with mock.patch('bluebottle.time_based.triggers.date') as mock_date:
                mock_date.today.return_value = when
                mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

                with mock.patch.object(
                    timezone, 'now',
                    return_value=timezone.get_current_timezone().localize(
                        datetime(when.year, when.month, when.day)
                    )
                ):
                    with_a_deadline_tasks()
                    period_application_tasks()
                    duration_tasks()

    def test_start(self):
        self.run_tasks(self.activity.start)
        self.refresh()

        self.assertEqual(
            self.application.contribution_values.get().status,
            'new'
        )

    def test_contribution_value_is_succeeded(self):
        self.run_tasks(self.activity.start)
        self.refresh()
        self.run_tasks(self.activity.start + timedelta(weeks=1, days=2))
        self.refresh()

        self.assertEqual(
            len(self.application.contribution_values.filter(status='new')),
            2
        )

        with mock.patch.object(
            timezone, 'now',
            return_value=timezone.get_current_timezone().localize(
                datetime.combine(self.activity.start, datetime.min.time()) + timedelta(weeks=1, days=1)
            )
        ):
            self.application.states.accept(save=True)

        self.assertEqual(
            len(self.application.contribution_values.filter(status='succeeded')),
            1
        )

        self.assertEqual(
            len(self.application.contribution_values.filter(status='new')),
            1
        )


class OngoingApplicationPeriodicTest(BluebottleTestCase):
    factory = OngoingActivityFactory
    application_factory = PeriodApplicationFactory

    def setUp(self):
        super().setUp()
        self.initiative = InitiativeFactory.create(status='approved')
        self.initiative.save()

        self.activity = self.factory.create(
            initiative=self.initiative,
            review=False,
            duration=timedelta(hours=2),
            duration_period='weeks'
        )
        self.activity.states.submit(save=True)
        self.application = self.application_factory.create(activity=self.activity)

    def run_tasks(self, when):
        with mock.patch('bluebottle.time_based.periodic_tasks.date') as mock_date:
            mock_date.today.return_value = when
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            with mock.patch('bluebottle.time_based.triggers.date') as mock_date:
                mock_date.today.return_value = when
                mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

                with mock.patch.object(
                    timezone, 'now',
                    return_value=timezone.get_current_timezone().localize(
                        datetime(when.year, when.month, when.day)
                    )
                ):
                    ongoing_tasks()
                    period_application_tasks()
                    duration_tasks()

    def refresh(self):
        with LocalTenant(self.tenant, clear_tenant=True):
            self.application.refresh_from_db()
            self.activity.refresh_from_db()

    def test_start(self):
        self.run_tasks(self.activity.start)
        self.refresh()

        self.assertEqual(
            self.application.contribution_values.get().status,
            'new'
        )

    def test_contribution_value_is_succeeded(self):
        self.run_tasks(self.activity.start)
        self.refresh()
        self.run_tasks(self.activity.start + timedelta(weeks=1, days=2))
        self.refresh()

        self.assertEqual(
            self.application.contribution_values.all()[0].status,
            'new'
        )

        self.assertEqual(
            self.application.contribution_values.all()[1].status,
            'succeeded'
        )

    def test_multiple_periods(self):
        for day in range(16):
            self.run_tasks(self.activity.start + timedelta(days=day))
            self.refresh()

        self.assertEqual(
            len(self.application.contribution_values.all()), 3
        )

        self.assertEqual(
            len(self.application.contribution_values.filter(status='succeeded')),
            2
        )

        self.assertEqual(
            len(self.application.contribution_values.filter(status='new')),
            1
        )

    def test_stop(self):
        self.test_multiple_periods()

        self.application.states.stop(save=True)

        for day in range(16, 22):
            self.run_tasks(self.activity.start + timedelta(days=day))
            self.refresh()

        self.assertEqual(
            len(self.application.contribution_values.all()), 3
        )

        self.assertEqual(
            len(self.application.contribution_values.filter(status='succeeded')),
            2
        )

        self.assertEqual(
            len(self.application.contribution_values.filter(status='failed')),
            1
        )

    def test_start_again(self):
        self.test_stop()

        self.application.states.start(save=True)

        for day in range(22, 30):
            self.run_tasks(self.activity.start + timedelta(days=day))
            self.refresh()

        self.assertEqual(
            len(self.application.contribution_values.all()), 5
        )

        self.assertEqual(
            len(self.application.contribution_values.filter(status='succeeded')),
            3
        )

        self.assertEqual(
            len(self.application.contribution_values.filter(status='new')),
            1
        )
        self.assertEqual(
            len(self.application.contribution_values.filter(status='failed')),
            1
        )
