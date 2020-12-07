from datetime import timedelta, date, datetime
from django.db import connection
import mock
from django.utils import timezone

from bluebottle.clients.utils import LocalTenant
from bluebottle.time_based.tasks import (
    on_a_date_tasks, with_a_deadline_tasks,
    period_participant_tasks, time_contribution_tasks
)
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, PeriodActivityFactory,
    DateParticipantFactory, PeriodParticipantFactory
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
        self.participant_factory.create(activity=self.activity)

        self.run_task(self.during)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'running')

    def test_succeed(self):
        self.assertEqual(self.activity.status, 'open')
        self.participant_factory.create(activity=self.activity)

        self.run_task(self.after)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'succeeded')


class DateActivityPeriodicTasksTest(TimeBasedActivityPeriodicTasksTestCase, BluebottleTestCase):
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory

    def run_task(self, when):
        with mock.patch.object(timezone, 'now', return_value=when):
            on_a_date_tasks()

    @property
    def during(self):
        return self.activity.start + timedelta(hours=1)

    @property
    def after(self):
        return self.activity.start + self.activity.duration + timedelta(hours=1)


class PeriodActivityPeriodicTasksTest(TimeBasedActivityPeriodicTasksTestCase, BluebottleTestCase):
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory

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


class PeriodParticipantPeriodicTest(BluebottleTestCase):
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory

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
        self.participant = self.participant_factory.create(activity=self.activity)

    def refresh(self):
        with LocalTenant(self.tenant, clear_tenant=True):
            self.participant.refresh_from_db()
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
                    period_participant_tasks()
                    time_contribution_tasks()

    def test_contribution_value_is_created(self):
        self.run_tasks(self.activity.start)
        self.refresh()

        self.assertEqual(
            self.participant.contributions.get().status,
            'new'
        )

    def test_contribution_value_is_succeeded(self):
        self.run_tasks(self.activity.start)

        self.run_tasks(self.activity.start + timedelta(weeks=1, days=1))
        self.refresh()

        self.assertEqual(
            len(self.participant.contributions.filter(status='succeeded')),
            1
        )

        self.assertEqual(
            len(self.participant.contributions.filter(status='new')),
            1
        )

    def test_contribution_value_is_succeeded_months(self):
        activity = self.factory.create(
            initiative=self.initiative,
            review=True,
            duration=timedelta(hours=2),
            duration_period='months',
            deadline=None
        )
        activity.states.submit(save=True)
        participant = self.participant_factory.create(activity=activity)
        participant.states.accept(save=True)

        self.run_tasks(activity.start + timedelta(minutes=1))
        self.run_tasks(activity.start + timedelta(weeks=1, days=1))

        participant.refresh_from_db()

        self.assertEqual(
            len(participant.contributions.filter(status='succeeded')),
            0
        )

        self.assertEqual(
            len(self.participant.contributions.filter(status='new')),
            1
        )

        self.run_tasks(activity.start + timedelta(weeks=5))

        participant.refresh_from_db()

        self.assertEqual(
            len(participant.contributions.filter(status='succeeded')),
            1
        )

        self.assertEqual(
            len(participant.contributions.filter(status='new')),
            1
        )

    def test_running_time(self):
        days = (self.activity.deadline - self.activity.start).days + 2

        for day in range(days):
            self.run_tasks(self.activity.start + timedelta(days=day))
            self.refresh()

        self.assertEqual(
            len(self.participant.contributions.all()), 3
        )

        self.assertEqual(
            len(self.participant.contributions.filter(status='succeeded')),
            2
        )

        self.assertEqual(
            len(self.participant.contributions.filter(status='new')),
            1
        )

    def test_cancel(self):
        days = (self.activity.deadline - self.activity.start).days + 2

        for day in range(days):
            self.run_tasks(self.activity.start + timedelta(days=day))
            self.refresh()

        self.assertEqual(
            len(self.participant.contributions.all()), 3
        )
        self.activity.states.cancel(save=True)

        for contribution in self.participant.contributions.all():
            self.assertEqual(contribution.status, 'failed')


class PeriodReviewParticipantPeriodicTest(BluebottleTestCase):
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory

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
        self.participant = self.participant_factory.create(activity=self.activity)

    def refresh(self):
        with LocalTenant(self.tenant, clear_tenant=True):
            self.participant.refresh_from_db()
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
                    period_participant_tasks()
                    time_contribution_tasks()

    def test_start(self):
        self.run_tasks(self.activity.start)
        self.refresh()

        self.assertEqual(
            self.participant.contributions.get().status,
            'new'
        )

    def test_contribution_value_is_succeeded(self):
        self.run_tasks(self.activity.start)
        self.refresh()
        self.run_tasks(self.activity.start + timedelta(weeks=1, days=2))
        self.refresh()

        self.assertEqual(
            len(self.participant.contributions.filter(status='new')),
            2
        )

        with mock.patch.object(
            timezone, 'now',
            return_value=timezone.get_current_timezone().localize(
                datetime.combine(self.activity.start, datetime.min.time()) + timedelta(weeks=1, days=1)
            )
        ):
            self.participant.states.accept(save=True)

        self.assertEqual(
            len(self.participant.contributions.filter(status='succeeded')),
            1
        )

        self.assertEqual(
            len(self.participant.contributions.filter(status='new')),
            1
        )
