from datetime import timedelta, date, datetime, time

import mock
import pytz
from django.contrib.gis.geos import Point
from django.core import mail
from django.db import connection
from django.template import defaultfilters
from django.utils import timezone
from django.utils.timezone import now, get_current_timezone
from pytz import UTC
from tenant_extras.utils import TenantLanguage

from bluebottle.clients.utils import LocalTenant
from bluebottle.initiatives.tests.factories import (
    InitiativeFactory
)
from bluebottle.notifications.models import Message
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tasks import (
    date_activity_tasks, with_a_deadline_tasks,
    period_participant_tasks, time_contribution_tasks, team_slot_tasks
)
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, PeriodActivityFactory,
    DateParticipantFactory, PeriodParticipantFactory, DateActivitySlotFactory,
    SlotParticipantFactory, TeamSlotFactory
)


class TimeBasedActivityPeriodicTasksTestCase():

    def setUp(self):
        super(TimeBasedActivityPeriodicTasksTestCase, self).setUp()
        self.initiative = InitiativeFactory.create(status='approved')
        self.initiative.save()

        self.activity = self.factory.create(initiative=self.initiative, review=False)

        if self.activity.states.submit:
            self.activity.states.submit(save=True)
        else:
            self.activity.states.publish(save=True)

        self.tenant = connection.tenant

    def test_nothing(self):
        self.assertEqual(self.activity.status, 'open')

        self.run_task(self.before)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

    def test_expired_after_registration_deadline(self):
        self.run_task(self.after_registration_deadline)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'expired')

    def test_full_after_registration_deadline(self):
        self.participant_factory.create(activity=self.activity)
        self.run_task(self.after_registration_deadline)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')


class DateActivityPeriodicTasksTest(TimeBasedActivityPeriodicTasksTestCase, BluebottleTestCase):
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory

    def setUp(self):
        super().setUp()
        self.activity.slots.all().delete()
        self.slot = DateActivitySlotFactory.create(
            activity=self.activity,
            title=None,
            start=datetime.combine((now() + timedelta(days=10)).date(), time(11, 30, tzinfo=UTC)),
            duration=timedelta(hours=3)
        )

    def run_task(self, when):
        with mock.patch.object(timezone, 'now', return_value=when):
            with mock.patch('bluebottle.time_based.periodic_tasks.date') as mock_date:
                mock_date.today.return_value = when.date()
                mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
                date_activity_tasks()

    @property
    def nigh(self):
        return timezone.get_current_timezone().localize(
            datetime(
                self.slot.start.year,
                self.slot.start.month,
                self.slot.start.day,
            )
        )

    @property
    def before(self):
        return timezone.get_current_timezone().localize(
            datetime(
                self.activity.registration_deadline.year,
                self.activity.registration_deadline.month,
                self.activity.registration_deadline.day
            ) - timedelta(days=1)
        )

    @property
    def after_registration_deadline(self):
        return timezone.get_current_timezone().localize(
            datetime(
                self.activity.registration_deadline.year,
                self.activity.registration_deadline.month,
                self.activity.registration_deadline.day
            ) + timedelta(days=1)
        )

    def test_reminder_single_date(self):
        eng = BlueBottleUserFactory.create(primary_language='en')
        DateParticipantFactory.create(
            activity=self.activity,
            user=eng,
            created=now() - timedelta(days=10)
        )
        mail.outbox = []
        self.run_task(self.nigh)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'The activity "{}" will take place tomorrow!'.format(self.activity.title)
        )
        with TenantLanguage('en'):
            expected = '{} {} - {} ({})'.format(
                defaultfilters.date(self.slot.start),
                defaultfilters.time(self.slot.start.astimezone(get_current_timezone())),
                defaultfilters.time(self.slot.end.astimezone(get_current_timezone())),
                self.slot.start.astimezone(get_current_timezone()).strftime('%Z'),
            )
        self.assertTrue(expected in mail.outbox[0].body)

        mail.outbox = []
        self.run_task(self.nigh)
        self.assertEqual(len(mail.outbox), 0, "Reminder mail should not be send again.")
        #  Duplicate this message to make sure the tasks doesn't hang on accidentally duplicated mails.
        message = Message.objects.last()
        message.id = None
        message.save()
        self.run_task(self.nigh)

    def test_reminder_different_timezone(self):
        self.slot.location = GeolocationFactory.create(
            position=Point(-74.2, 40.7)
        )
        self.slot.save()

        eng = BlueBottleUserFactory.create(primary_language='en')
        DateParticipantFactory.create(
            activity=self.activity,
            user=eng,
            created=now() - timedelta(days=10)
        )
        mail.outbox = []
        self.run_task(self.nigh)
        self.assertEqual(
            mail.outbox[0].subject,
            'The activity "{}" will take place tomorrow!'.format(self.activity.title)
        )
        with TenantLanguage('en'):
            tz = pytz.timezone(self.slot.location.timezone)
            expected = '{} {} - {} ({})'.format(
                defaultfilters.date(self.slot.start),
                defaultfilters.time(self.slot.start.astimezone(tz)),
                defaultfilters.time(self.slot.end.astimezone(tz)),
                self.slot.start.astimezone(tz).strftime('%Z'),
            )
        self.assertTrue(expected in mail.outbox[0].body)

        self.assertTrue(
            "a.m." in mail.outbox[0].body,
            "Time strings should really be English format"
        )

    def test_reminder_single_date_dutch(self):
        nld = BlueBottleUserFactory.create(primary_language='nl')
        DateParticipantFactory.create(
            activity=self.activity,
            user=nld,
            created=now() - timedelta(days=10)
        )
        mail.outbox = []
        self.run_task(self.nigh)
        self.assertEqual(
            mail.outbox[0].subject,
            'The activity "{}" will take place tomorrow!'.format(self.activity.title)
        )
        with TenantLanguage('nl'):
            expected = '{} {} - {} ({})'.format(
                defaultfilters.date(self.slot.start),
                defaultfilters.time(self.slot.start.astimezone(get_current_timezone())),
                defaultfilters.time(self.slot.end.astimezone(get_current_timezone())),
                self.slot.start.astimezone(get_current_timezone()).strftime('%Z'),
            )

        self.assertTrue(expected in mail.outbox[0].body)
        self.assertTrue(
            "a.m." not in mail.outbox[0].body,
            "Time strings should really be Dutch format"
        )

    def test_reminder_multiple_dates(self):
        self.slot.title = "First slot"
        self.slot.save()
        self.slot2 = DateActivitySlotFactory.create(
            activity=self.activity,
            title='Slot 2',
            start=datetime.combine((now() + timedelta(days=11)).date(), time(14, 0, tzinfo=UTC)),
            duration=timedelta(hours=3)
        )
        eng = BlueBottleUserFactory.create(primary_language='eng')
        DateParticipantFactory.create(
            activity=self.activity,
            user=eng,
            created=now() - timedelta(days=10)
        )
        mail.outbox = []
        self.run_task(self.nigh)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'The activity "{}" will take place tomorrow!'.format(
                self.activity.title
            )
        )
        with TenantLanguage('en'):
            expected = '{} {} - {} ({})'.format(
                defaultfilters.date(self.slot.start),
                defaultfilters.time(self.slot.start.astimezone(get_current_timezone())),
                defaultfilters.time(self.slot.end.astimezone(get_current_timezone())),
                self.slot.start.astimezone(get_current_timezone()).strftime('%Z'),
            )
        self.assertTrue(expected in mail.outbox[0].body)
        mail.outbox = []
        self.run_task(self.nigh)
        self.assertEqual(len(mail.outbox), 0, "Should only send reminders once")

    def test_finished_multiple_dates(self):
        self.slot.title = "First slot"
        self.slot.save()
        self.slot2 = DateActivitySlotFactory.create(
            activity=self.activity,
            title='Slot 2',
            start=now() - timedelta(days=11),
            duration=timedelta(hours=3),
            status='open'
        )
        self.activity.slot_selection = 'free'
        self.activity.save()

        participant = DateParticipantFactory.create(
            activity=self.activity,
            created=now() - timedelta(days=10)
        )
        SlotParticipantFactory.create(
            slot=self.slot,
            participant=participant
        )
        SlotParticipantFactory.create(
            slot=self.slot2,
            participant=participant
        )
        self.run_task(now())
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'open')

        # Close first slot too
        self.slot.start = now() - timedelta(days=11)
        self.slot.status = 'finished'
        self.slot.save()

        self.run_task(now())
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'succeeded')

    def test_finished_expired_slot(self):

        activity = DateActivityFactory.create(
            slot_selection='all',
            owner=BlueBottleUserFactory.create(),
            status='open',
            slots=[]
        )
        slot = DateActivitySlotFactory.create(
            activity=activity,
            start=now() + timedelta(days=1),
            capacity=5,
            duration=timedelta(hours=3)
        )

        self.run_task(now() + timedelta(days=1))
        activity.refresh_from_db()
        slot.refresh_from_db()
        self.assertEqual(slot.status, 'running')
        self.assertEqual(activity.status, 'open')
        self.run_task(now() + timedelta(days=2))
        activity.refresh_from_db()
        slot.refresh_from_db()
        self.assertEqual(slot.status, 'finished')
        self.assertEqual(activity.status, 'expired')

    def test_finished_multiple_past_dates(self):
        self.slot.title = "First slot"
        self.slot.save()
        self.slot2 = DateActivitySlotFactory.create(
            activity=self.activity,
            title='Slot 2',
            start=datetime.combine((now() - timedelta(days=11)).date(), time(14, 0, tzinfo=UTC)),
            duration=timedelta(hours=3)
        )
        eng = BlueBottleUserFactory.create(primary_language='eng')
        DateParticipantFactory.create(
            activity=self.activity,
            user=eng,
            created=now() - timedelta(days=10)
        )
        mail.outbox = []
        self.run_task(self.nigh)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'The activity "{}" will take place tomorrow!'.format(
                self.activity.title
            )
        )
        with TenantLanguage('en'):
            expected = '{} {} - {} ({})'.format(
                defaultfilters.date(self.slot.start),
                defaultfilters.time(self.slot.start.astimezone(get_current_timezone())),
                defaultfilters.time(self.slot.end.astimezone(get_current_timezone())),
                self.slot.start.astimezone(get_current_timezone()).strftime('%Z'),
            )
        self.assertTrue(expected in mail.outbox[0].body)
        mail.outbox = []
        self.run_task(self.nigh)
        self.assertEqual(len(mail.outbox), 0, "Should only send reminders once")


class PeriodActivityPeriodicTasksTest(TimeBasedActivityPeriodicTasksTestCase, BluebottleTestCase):
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory

    def run_task(self, when):
        with mock.patch('bluebottle.time_based.periodic_tasks.date') as mock_date:
            mock_date.today.return_value = when
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            with_a_deadline_tasks()

    @property
    def after_registration_deadline(self):
        return self.activity.registration_deadline + timedelta(days=1)

    @property
    def before(self):
        return self.activity.registration_deadline - timedelta(days=1)

    @property
    def during(self):
        return self.activity.start

    @property
    def after(self):
        return self.activity.deadline + timedelta(days=1)

    def test_expire(self):
        self.assertEqual(self.activity.status, 'open')

        self.run_task(self.after)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'expired')

    def test_expire_after_start(self):
        self.assertEqual(self.activity.status, 'open')

        self.run_task(self.during)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'expired')

    def test_succeed(self):
        self.assertEqual(self.activity.status, 'open')
        self.participant_factory.create(activity=self.activity)

        self.run_task(self.after)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'succeeded')


class OverallPeriodParticipantPeriodicTest(BluebottleTestCase):
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory

    def setUp(self):
        super().setUp()
        self.initiative = InitiativeFactory.create(status='approved')
        self.initiative.save()
        start = date.today() + timedelta(days=10)
        deadline = date.today() + timedelta(days=26)

        self.activity = self.factory.create(
            initiative=self.initiative,
            review=False,
            start=start,
            deadline=deadline,
            duration=timedelta(hours=2),
            duration_period='overall'
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

                with mock.patch('bluebottle.time_based.effects.date') as mock_date:
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

    def test_no_contribution_create(self):
        self.participant.current_period = now()

        self.run_tasks(self.activity.start + timedelta(weeks=1, days=1))
        self.run_tasks(self.activity.start + timedelta(weeks=2, days=1))
        self.run_tasks(self.activity.start + timedelta(weeks=3, days=1))

        self.assertEqual(len(self.participant.contributions.all()), 1)


class PeriodParticipantPeriodicTest(BluebottleTestCase):
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory

    def setUp(self):
        super().setUp()
        self.initiative = InitiativeFactory.create(status='approved')
        self.initiative.save()
        start = date.today() + timedelta(days=10)
        deadline = date.today() + timedelta(days=26)

        self.activity = self.factory.create(
            initiative=self.initiative,
            review=False,
            start=start,
            deadline=deadline,
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

                with mock.patch('bluebottle.time_based.effects.date') as mock_date:
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

    def test_contribution_value_is_created_and_succeeded_instantly(self):
        self.run_tasks(self.activity.start)
        self.refresh()

        self.assertEqual(
            self.participant.contributions.get().status,
            'succeeded'
        )

    def test_contribution_value_is_still_succeeded(self):
        self.run_tasks(self.activity.start)

        self.run_tasks(self.activity.start + timedelta(weeks=1, days=1))
        self.refresh()

        self.assertEqual(
            len(self.participant.contributions.filter(status='succeeded')),
            2
        )

    def test_contribution_value_is_succeeded_each_month(self):
        activity = self.factory.create(
            initiative=self.initiative,
            duration=timedelta(hours=2),
            duration_period='months',
            deadline=None
        )
        activity.states.submit(save=True)
        participant = self.participant_factory.create(activity=activity)

        self.run_tasks(activity.start + timedelta(minutes=1))
        self.run_tasks(activity.start + timedelta(weeks=1, days=1))

        participant.refresh_from_db()

        self.assertEqual(
            len(participant.contributions.filter(status='succeeded')),
            1
        )

        self.run_tasks(activity.start + timedelta(weeks=5))

        participant.refresh_from_db()

        self.assertEqual(
            len(participant.contributions.filter(status='succeeded')),
            2
        )

    def test_running_time(self):
        today = date.today()
        while today <= self.activity.deadline + timedelta(days=1):
            self.run_tasks(today)
            self.refresh()
            today += timedelta(days=1)

        self.assertEqual(
            len(self.participant.contributions.all()), 3
        )

        self.assertEqual(
            len(self.participant.contributions.filter(status='succeeded')),
            3
        )
        tz = timezone.get_current_timezone()

        first = self.participant.contributions.order_by('start').first()
        self.assertEqual(first.start.astimezone(tz).date(), self.activity.start)

        last = self.participant.contributions.order_by('start').last()
        self.assertEqual(last.end.astimezone(tz).date(), self.activity.deadline)

    def test_running_time_stop_and_start(self):
        today = date.today()
        while today <= self.activity.deadline + timedelta(days=1):
            self.run_tasks(today)
            if today == self.activity.start + timedelta(days=5):
                self.participant.states.stop(save=True)

            if today == self.activity.start + timedelta(days=10):
                self.participant.states.start(save=True)

            self.refresh()
            today += timedelta(days=1)

        self.assertEqual(
            len(self.participant.contributions.all()), 2
        )

        self.assertEqual(
            len(self.participant.contributions.filter(status='succeeded')),
            2
        )
        tz = timezone.get_current_timezone()

        first = self.participant.contributions.order_by('start').first()
        self.assertEqual(first.start.astimezone(tz).date(), self.activity.start)

        last = self.participant.contributions.order_by('start').last()
        self.assertEqual(last.end.astimezone(tz).date(), self.activity.deadline)

    def test_running_time_no_start(self):
        self.activity.start = None
        self.activity.save()

        self.participant = self.participant_factory.create(activity=self.activity)

        today = date.today()
        while today <= self.activity.deadline + timedelta(days=1):
            self.run_tasks(today)
            self.refresh()
            today += timedelta(days=1)

        self.assertEqual(
            len(self.participant.contributions.all()), 4
        )

        self.assertEqual(
            len(self.participant.contributions.filter(status='succeeded')),
            4
        )
        tz = timezone.get_current_timezone()

        first = self.participant.contributions.order_by('start').first()
        self.assertEqual(first.start.astimezone(tz).date(), date.today())

        last = self.participant.contributions.order_by('start').last()
        self.assertEqual(last.end.astimezone(tz).date(), self.activity.deadline)

    def test_cancel(self):
        today = date.today()
        while today <= self.activity.deadline + timedelta(days=1):
            self.run_tasks(today)
            self.refresh()
            today += timedelta(days=1)

        self.assertEqual(
            len(self.participant.contributions.all()), 3
        )
        self.activity.states.cancel(save=True)

        for contribution in self.participant.contributions.all():
            self.assertEqual(contribution.status, 'failed')


class SlotActivityPeriodicTasksTest(BluebottleTestCase):

    def setUp(self):
        self.initiative = InitiativeFactory.create(status='approved')
        self.initiative.save()
        self.activity = DateActivityFactory.create(initiative=self.initiative, review=False)
        self.activity.states.publish(save=True)
        self.slot = DateActivitySlotFactory.create(activity=self.activity)
        self.tenant = connection.tenant

    @property
    def before(self):
        return self.slot.start - timedelta(days=1)

    @property
    def during(self):
        return self.slot.start + timedelta(seconds=10)

    @property
    def after(self):
        return self.slot.start + self.slot.duration + timedelta(seconds=10)

    def run_task(self, when):
        with mock.patch.object(timezone, 'now', return_value=when):
            with mock.patch('bluebottle.time_based.periodic_tasks.date') as mock_date:
                mock_date.today.return_value = when.date()
                mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
                date_activity_tasks()

    def test_finish(self):
        self.assertEqual(self.slot.status, 'open')

        self.run_task(self.after)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.slot.refresh_from_db()

        self.assertEqual(self.slot.status, 'finished')
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'expired')

    def test_finish_with_participants(self):
        self.assertEqual(self.slot.status, 'open')
        self.participant = DateParticipantFactory.create(activity=self.activity)

        self.run_task(self.after)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.slot.refresh_from_db()

        self.assertEqual(self.slot.status, 'finished')
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'succeeded')

    def test_finish_free(self):
        self.activity = DateActivityFactory.create(
            slot_selection='free', initiative=self.initiative, review=False
        )
        self.activity.states.publish(save=True)
        self.slot = DateActivitySlotFactory.create(activity=self.activity)
        self.assertEqual(self.slot.status, 'open')
        self.participant = DateParticipantFactory.create(activity=self.activity)
        SlotParticipantFactory(slot=self.slot, participant=self.participant)

        self.run_task(self.after)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.slot.refresh_from_db()

        self.assertEqual(self.slot.status, 'finished')
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'succeeded')

    def test_after_start_dont_expire(self):
        self.assertEqual(self.slot.status, 'open')

        self.run_task(self.during)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.slot.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

    def test_start(self):
        self.assertEqual(self.slot.status, 'open')
        self.participant = DateParticipantFactory.create(activity=self.activity)

        self.run_task(self.during)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.slot.refresh_from_db()

        self.assertEqual(self.slot.status, 'running')

    def test_succeed(self):
        self.assertEqual(self.slot.status, 'open')
        self.participant = DateParticipantFactory.create(activity=self.activity)

        self.run_task(self.after)

        with LocalTenant(self.tenant, clear_tenant=True):
            self.slot.refresh_from_db()

        self.assertEqual(self.slot.status, 'finished')


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
        self.participant = self.participant_factory.build(activity=self.activity)
        self.participant.user.save()
        self.participant.execute_triggers(user=self.participant.user, send_messages=True)
        self.participant.save()

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

                with mock.patch('bluebottle.time_based.effects.date') as mock_date:
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
            'succeeded'
        )

    def test_contribution_value_is_succeeded(self):
        today = date.today()
        while today <= self.activity.deadline - timedelta(days=2):
            self.run_tasks(today)
            self.refresh()
            today += timedelta(days=1)

        self.assertEqual(
            len(self.participant.contributions.filter(status='new')),
            0
        )
        self.assertEqual(
            len(self.participant.contributions.filter(status='succeeded')),
            2
        )

        with mock.patch.object(
                timezone, 'now',
                return_value=timezone.get_current_timezone().localize(
                    datetime(today.year, today.month, today.day)
                )
        ):
            self.participant.states.accept(save=True)

        self.assertEqual(
            len(self.participant.contributions.filter(status='succeeded')),
            2
        )


class TeamSlotPeriodicTasksTest(BluebottleTestCase):

    def setUp(self):
        self.activity = PeriodActivityFactory.create(
            team_activity='teams',
            status='open'
        )
        self.participant = PeriodParticipantFactory.create(
            activity=self.activity
        )
        self.slot = TeamSlotFactory.create(
            activity=self.activity,
            team=self.participant.team,
            start=datetime.combine((now() + timedelta(days=10)).date(), time(11, 30, tzinfo=UTC)),
            duration=timedelta(hours=3)
        )

    def run_task(self, when):
        with mock.patch.object(timezone, 'now', return_value=when):
            with mock.patch('bluebottle.time_based.periodic_tasks.date') as mock_date:
                mock_date.today.return_value = when.date()
                mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
                team_slot_tasks()

    @property
    def nigh(self):
        return timezone.get_current_timezone().localize(
            datetime(
                self.slot.start.year,
                self.slot.start.month,
                self.slot.start.day
            ) - timedelta(days=4)
        )

    @property
    def current(self):
        return self.slot.start + timedelta(hours=1)

    @property
    def after(self):
        return self.slot.start + timedelta(days=2)

    @property
    def before(self):
        return timezone.get_current_timezone().localize(
            datetime(
                self.activity.registration_deadline.year,
                self.activity.registration_deadline.month,
                self.activity.registration_deadline.day
            ) - timedelta(days=1)
        )

    def assertStatus(self, obj, status):
        obj.refresh_from_db()
        return self.assertEqual(obj.status, status)

    def test_reminder_team_slot(self):
        mail.outbox = []
        self.run_task(self.nigh)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'The team activity "{}" will take place tomorrow!'.format(self.activity.title)
        )
        self.assertTrue('The team activity is just a few days away!' in mail.outbox[0].body)

        mail.outbox = []
        self.run_task(self.nigh)
        self.assertEqual(len(mail.outbox), 0, "Reminder mail should not be send again.")

    def test_start_team_slot(self):
        mail.outbox = []
        self.run_task(self.current)
        self.assertStatus(self.slot, 'running')
        self.assertStatus(self.slot.team, 'running')

    def test_finish_team_slot(self):
        mail.outbox = []
        self.run_task(self.after)
        self.assertStatus(self.slot, 'finished')
        self.assertStatus(self.slot.team, 'finished')
        self.assertStatus(self.participant.contributions.first(), 'succeeded')

    def test_finish_cancelled_team(self):
        mail.outbox = []
        self.participant.team.states.cancel(save=True)
        self.run_task(self.after)

        self.assertStatus(self.slot, 'cancelled')
        self.assertStatus(self.slot.team, 'cancelled')
        self.assertStatus(self.participant, 'accepted')
        self.assertStatus(self.participant.contributions.first(), 'failed')

    def test_finish_restore_team(self):
        mail.outbox = []
        self.participant.team.states.cancel(save=True)
        self.participant.team.states.reopen(save=True)
        self.run_task(self.after)

        self.assertStatus(self.slot, 'finished')
        self.assertStatus(self.slot.team, 'finished')
        self.assertStatus(self.participant, 'accepted')
        self.assertStatus(self.participant.contributions.first(), 'succeeded')

    def test_finish_withdrawn_team(self):
        mail.outbox = []
        self.participant.team.states.withdraw(save=True)
        self.run_task(self.after)

        self.assertStatus(self.slot, 'cancelled')
        self.assertStatus(self.slot.team, 'withdrawn')
        self.assertStatus(self.participant, 'accepted')
        self.assertStatus(self.participant.contributions.first(), 'failed')

    def test_finish_reapply_team(self):
        mail.outbox = []
        self.participant.team.states.withdraw(save=True)
        self.participant.team.states.reapply(save=True)
        self.run_task(self.after)

        self.assertStatus(self.slot, 'finished')
        self.assertStatus(self.slot.team, 'finished')
        self.assertStatus(self.participant, 'accepted')
        self.assertStatus(self.participant.contributions.first(), 'succeeded')

    def test_finish_withdrawn_team_member(self):
        mail.outbox = []
        self.participant.states.withdraw(save=True)
        self.run_task(self.after)

        self.assertStatus(self.slot, 'finished')
        self.assertStatus(self.slot.team, 'finished')
        self.assertStatus(self.participant, 'withdrawn')
        self.assertStatus(self.participant.contributions.first(), 'failed')

    def test_finish_reapplied_team_member(self):
        mail.outbox = []
        self.participant.states.withdraw(save=True)
        self.participant.states.reapply(save=True)
        self.run_task(self.after)

        self.assertStatus(self.slot, 'finished')
        self.assertStatus(self.slot.team, 'finished')
        self.assertStatus(self.participant, 'accepted')
        self.assertStatus(self.participant.contributions.first(), 'succeeded')
