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
    date_activity_tasks,
    periodic_activity_tasks,
    periodic_slot_tasks,
    schedule_activity_tasks,
    schedule_slot_tasks,
    team_schedule_slot_tasks,
)
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateParticipantFactory, DateActivitySlotFactory,
    PeriodicActivityFactory,
    PeriodicRegistrationFactory,
    ScheduleActivityFactory,
    ScheduleParticipantFactory,
    ScheduleSlotFactory,
    SlotParticipantFactory,
    TeamFactory,
    TeamMemberFactory,
)


class TimeBasedActivityPeriodicTasksTestCase():
    def setUp(self):
        super(TimeBasedActivityPeriodicTasksTestCase, self).setUp()
        self.initiative = InitiativeFactory.create(status='approved')
        self.initiative.save()

        self.activity = self.factory.create(initiative=self.initiative, review=False)

        if self.activity.states.submit:
            self.activity.states.publish(save=True)
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

    def assertStatus(self, obj, status):
        obj.refresh_from_db()
        return self.assertEqual(obj.status, status)

    @property
    def almost(self):
        return self.slot.start - timedelta(hours=3)

    @property
    def nigh(self):
        return self.slot.start - timedelta(hours=22)

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
        participant = DateParticipantFactory.create(
            activity=self.activity,
            user=eng,
            created=now() - timedelta(days=10)
        )
        SlotParticipantFactory.create(participant=participant, slot=self.slot)
        mail.outbox = []
        self.run_task(self.nigh)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'The activity "{}" will take place tomorrow!'.format(self.activity.title)
        )
        with TenantLanguage('en'):
            expected_date = defaultfilters.date(self.slot.start)
            expected_time = '{} to {} ({})'.format(
                defaultfilters.time(self.slot.start.astimezone(get_current_timezone())),
                defaultfilters.time(self.slot.end.astimezone(get_current_timezone())),
                self.slot.start.astimezone(get_current_timezone()).strftime('%Z'),
            )

        self.assertTrue(expected_date in mail.outbox[0].body)
        self.assertTrue(expected_time in mail.outbox[0].body)

        mail.outbox = []
        self.run_task(self.nigh)
        self.assertEqual(len(mail.outbox), 0, "Reminder mail should not be send again.")
        #  Duplicate this message to make sure the tasks doesn't hang on accidentally duplicated mails.
        message = Message.objects.last()
        message.id = None
        message.save()
        self.run_task(self.nigh)

    def test_no_reminder_almost_started(self):
        eng = BlueBottleUserFactory.create(primary_language='en')
        participant = DateParticipantFactory.create(
            activity=self.activity,
            user=eng,
        )
        SlotParticipantFactory.create(participant=participant, slot=self.slot)
        mail.outbox = []
        self.run_task(self.almost)
        self.assertEqual(len(mail.outbox), 0)

    def test_reminder_different_timezone(self):
        self.slot.location = GeolocationFactory.create(
            position=Point(-74.2, 40.7)
        )
        self.slot.save()

        eng = BlueBottleUserFactory.create(primary_language='en')
        participant = DateParticipantFactory.create(
            activity=self.activity,
            user=eng,
            created=now() - timedelta(days=10)
        )
        SlotParticipantFactory.create(participant=participant, slot=self.slot)
        mail.outbox = []
        self.run_task(self.nigh)
        self.assertEqual(
            mail.outbox[0].subject,
            'The activity "{}" will take place tomorrow!'.format(self.activity.title)
        )
        with TenantLanguage('en'):
            tz = pytz.timezone(self.slot.location.timezone)
            expected_date = defaultfilters.date(self.slot.start)
            expected_time = '{} to {} ({})'.format(
                defaultfilters.time(self.slot.start.astimezone(tz)),
                defaultfilters.time(self.slot.end.astimezone(tz)),
                self.slot.start.astimezone(tz).strftime('%Z'),
            )

        self.assertTrue(expected_date in mail.outbox[0].body)
        self.assertTrue(expected_time in mail.outbox[0].body)

        self.assertTrue(
            "a.m." in mail.outbox[0].body,
            "Time strings should really be English format"
        )

    def test_reminder_single_date_dutch(self):
        nld = BlueBottleUserFactory.create(primary_language='nl')
        participant = DateParticipantFactory.create(
            activity=self.activity,
            user=nld,
            created=now() - timedelta(days=10)
        )
        SlotParticipantFactory.create(participant=participant, slot=self.slot)
        mail.outbox = []
        self.run_task(self.nigh)
        self.assertEqual(
            mail.outbox[0].subject,
            'The activity "{}" will take place tomorrow!'.format(self.activity.title)
        )
        with TenantLanguage('nl'):
            expected_date = defaultfilters.date(self.slot.start)
            expected_time = '{} to {} ({})'.format(
                defaultfilters.time(self.slot.start.astimezone(get_current_timezone())),
                defaultfilters.time(self.slot.end.astimezone(get_current_timezone())),
                self.slot.start.astimezone(get_current_timezone()).strftime('%Z'),
            )

        self.assertTrue(expected_date in mail.outbox[0].body)
        self.assertTrue(expected_time in mail.outbox[0].body)

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
        participant = DateParticipantFactory.create(
            activity=self.activity,
            user=eng,
            created=now() - timedelta(days=10)
        )
        SlotParticipantFactory.create(participant=participant, slot=self.slot)
        SlotParticipantFactory.create(participant=participant, slot=self.slot2)

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
            expected_date = defaultfilters.date(self.slot.start)
            expected_time = '{} to {} ({})'.format(
                defaultfilters.time(self.slot.start.astimezone(get_current_timezone())),
                defaultfilters.time(self.slot.end.astimezone(get_current_timezone())),
                self.slot.start.astimezone(get_current_timezone()).strftime('%Z'),
            )

        self.assertTrue(expected_date in mail.outbox[0].body)
        self.assertTrue(expected_time in mail.outbox[0].body)
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

    def test_finished_started_slot(self):

        activity = DateActivityFactory.create(
            owner=BlueBottleUserFactory.create(),
            review=False,
            status='open',
            slots=[]
        )
        slot = DateActivitySlotFactory.create(
            activity=activity,
            start=now() + timedelta(days=1),
            capacity=5,
            duration=timedelta(hours=3)
        )

        participant = DateParticipantFactory.create(
            activity=activity,
            status='accepted'
        )

        SlotParticipantFactory.create(
            slot=slot,
            participant=participant
        )

        self.run_task(now() + timedelta(days=1))
        activity.refresh_from_db()
        slot.refresh_from_db()
        self.assertEqual(slot.status, 'running')
        self.assertEqual(activity.status, 'full')

        self.run_task(now() + timedelta(days=2))
        activity.refresh_from_db()
        slot.refresh_from_db()
        self.assertEqual(slot.status, 'finished')
        self.assertEqual(activity.status, 'succeeded')

    def test_finished_expired_slot(self):

        activity = DateActivityFactory.create(
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
        self.assertEqual(activity.status, 'full')
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
        participant = DateParticipantFactory.create(
            activity=self.activity,
            user=eng,
            created=now() - timedelta(days=10)
        )
        SlotParticipantFactory.create(participant=participant, slot=self.slot)
        SlotParticipantFactory.create(participant=participant, slot=self.slot2)
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
            expected_date = defaultfilters.date(self.slot.start)
            expected_time = '{} to {} ({})'.format(
                defaultfilters.time(self.slot.start.astimezone(get_current_timezone())),
                defaultfilters.time(self.slot.end.astimezone(get_current_timezone())),
                self.slot.start.astimezone(get_current_timezone()).strftime('%Z'),
            )

        self.assertTrue(expected_date in mail.outbox[0].body)
        self.assertTrue(expected_time in mail.outbox[0].body)
        mail.outbox = []
        self.run_task(self.nigh)
        self.assertEqual(len(mail.outbox), 0, "Should only send reminders once")

    def test_finished_withdrawn_slot(self):

        activity = DateActivityFactory.create(
            owner=BlueBottleUserFactory.create(),
            review=False,
            status='open',
            slots=[]
        )
        slot = DateActivitySlotFactory.create(
            activity=activity,
            start=now() + timedelta(days=1),
            capacity=5,
            duration=timedelta(hours=3)
        )

        participant = DateParticipantFactory.create(
            activity=activity,
            status='accepted'
        )

        SlotParticipantFactory.create(
            slot=slot,
            participant=participant
        )

        splitter = DateParticipantFactory.create(
            activity=activity,
            status='accepted'
        )

        slot_participant = SlotParticipantFactory.create(
            slot=slot,
            participant=splitter
        )

        contribution = splitter.contributions.first()
        slot_participant.states.withdraw(save=True)

        self.assertStatus(splitter, 'accepted')
        self.assertStatus(slot_participant, 'withdrawn')
        self.assertStatus(contribution, 'failed')

        self.run_task(now() + timedelta(days=3))
        activity.refresh_from_db()

        self.assertStatus(splitter, 'accepted')
        self.assertStatus(slot_participant, 'withdrawn')
        self.assertStatus(contribution, 'failed')


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
            initiative=self.initiative, review=False
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


class PeriodicActivityPeriodicTaskTestCase(BluebottleTestCase):
    factory = PeriodicActivityFactory

    def setUp(self):
        super(PeriodicActivityPeriodicTaskTestCase, self).setUp()
        self.initiative = InitiativeFactory.create(status='approved')
        self.initiative.save()

        self.activity = self.factory.create(
            title='A nice time',
            initiative=self.initiative,
            review=False,
            start=date.today() + timedelta(days=5),
            deadline=date.today() + timedelta(days=40),
            registration_deadline=None,
            period="weeks"
        )
        self.activity.states.publish(save=True)

    def run_task(self, when):
        tz = get_current_timezone()

        with mock.patch.object(
            timezone,
            'now',
            return_value=tz.localize(
                datetime.combine(when, datetime.min.time())
            )
        ):
            with mock.patch('bluebottle.time_based.periodic_tasks.date') as mock_date:
                mock_date.today.return_value = when
                mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
                periodic_activity_tasks()
                periodic_slot_tasks()

        with LocalTenant(connection.tenant, clear_tenant=True):
            self.activity.refresh_from_db()

    @property
    def before(self):
        return self.activity.start - timedelta(days=1)

    @property
    def started(self):
        return self.activity.start + timedelta(days=1)

    @property
    def next_period(self):
        return self.activity.start + timedelta(days=8)

    @property
    def finished(self):
        return self.activity.deadline + timedelta(days=1)

    def test_before(self):
        self.run_task(self.before)
        self.assertEqual(self.activity.slots.count(), 1)
        self.assertEqual(self.activity.slots.first().status, 'new')

    def test_started(self):
        self.run_task(self.started)
        self.assertEqual(self.activity.slots.count(), 1)
        self.assertEqual(self.activity.slots.first().status, "running")
        self.assertEqual(self.activity.status, "open")

    def test_next_slot(self):
        self.participant = PeriodicRegistrationFactory.create(activity=self.activity)

        self.run_task(self.started)
        self.run_task(self.next_period)

        self.assertEqual(self.activity.slots.count(), 2)

        self.assertEqual(self.activity.status, "open")
        self.assertEqual(
            self.activity.slots.order_by("start").first().status, "finished"
        )
        self.assertEqual(
            self.activity.slots.order_by("-start").first().status, "running"
        )

    def test_succeed(self):
        user = BlueBottleUserFactory.create()
        self.registration = PeriodicRegistrationFactory.create(
            activity=self.activity,
            user=user,
            as_user=user
        )
        self.participant = self.registration.participants.first()
        self.run_task(self.finished)

        self.assertEqual(self.activity.status, 'succeeded')

    def test_cancelled(self):
        self.run_task(self.finished)

        self.assertEqual(self.activity.status, 'expired')

    def test_reminder_monthly_email(self):
        self.activity.deadline = date.today() + timedelta(weeks=100)
        self.activity.period = 'months'
        self.activity.save()
        registration = PeriodicRegistrationFactory.create(activity=self.activity)
        registration.states.accept(save=True)

        mail.outbox = []
        for n in range(1, 7):
            month = self.activity.start + timedelta(days=n * 31)
            self.run_task(month)
            if n == 1:
                self.assertEqual(registration.participants.count(), 2)
                self.assertEqual(self.activity.slots.count(), 2)
                self.assertEqual(len(mail.outbox), 0)
            if n == 2:
                self.assertEqual(registration.participants.count(), 3)
                self.assertEqual(self.activity.slots.count(), 3)
                self.assertEqual(len(mail.outbox), 1)
                self.assertEqual(mail.outbox[0].subject, '⏰ Reminder: Update your participation!')
            if n == 4:
                self.assertEqual(registration.participants.count(), 5)
                self.assertEqual(self.activity.slots.count(), 5)
                self.assertEqual(len(mail.outbox), 3)
                registration.states.stop(save=True)
            if n == 5:
                self.assertEqual(registration.participants.count(), 5)
                self.assertEqual(self.activity.slots.count(), 6)
                self.assertEqual(len(mail.outbox), 5)
                self.assertHasMail(
                    'Your contribution to the activity "A nice time" has been stopped'
                )
                self.assertHasMail(
                    'A participant for your activity "A nice time" has stopped'
                )
            if n == 7:
                self.assertEqual(registration.participants.count(), 5)
                self.assertEqual(self.activity.slots.count(), 8)
                self.assertEqual(len(mail.outbox), 5)

    def test_reminder_weekly_email(self):
        self.activity.deadline = date.today() + timedelta(weeks=10)
        self.activity.save()
        registration = PeriodicRegistrationFactory.create(activity=self.activity)
        registration.states.accept(save=True)

        mail.outbox = []
        for n in range(1, 7):
            week = self.activity.start + timedelta(weeks=n)
            self.run_task(week)
            if n == 2:
                self.assertEqual(registration.participants.count(), 3)
                self.assertEqual(self.activity.slots.count(), 3)
                self.assertEqual(len(mail.outbox), 0)
            if n == 3:
                self.assertEqual(registration.participants.count(), 4)
                self.assertEqual(self.activity.slots.count(), 4)
                self.assertEqual(len(mail.outbox), 1)
                self.assertEqual(mail.outbox[0].subject, '⏰ Reminder: Update your participation!')
            if n == 4:
                self.assertEqual(registration.participants.count(), 5)
                self.assertEqual(self.activity.slots.count(), 5)
                self.assertEqual(len(mail.outbox), 2)
                self.assertEqual(mail.outbox[1].subject, '⏰ Reminder: Update your participation!')
                registration.states.stop(save=True)
            if n == 5:
                self.assertEqual(registration.participants.count(), 5)
                self.assertEqual(self.activity.slots.count(), 6)
                self.assertEqual(len(mail.outbox), 4)
                self.assertEqual(mail.outbox[0].subject, '⏰ Reminder: Update your participation!')
                self.assertEqual(mail.outbox[1].subject, '⏰ Reminder: Update your participation!')
                self.assertEqual(
                    mail.outbox[2].subject,
                    'Your contribution to the activity "A nice time" has been stopped'
                )
                self.assertEqual(
                    mail.outbox[3].subject,
                    'A participant for your activity "A nice time" has stopped'
                )
            if n == 6:
                self.assertEqual(registration.participants.count(), 5)
                self.assertEqual(self.activity.slots.count(), 7)
                self.assertEqual(len(mail.outbox), 4)

    def test_reminder_daily_email(self):
        activity = PeriodicActivityFactory.create(
            title='A nice time',
            initiative=self.initiative,
            review=True,
            start=date.today(),
            deadline=date.today() + timedelta(days=40),
            registration_deadline=None,
            period="days"
        )
        activity.states.publish(save=True)
        start = now()
        registration = PeriodicRegistrationFactory.create(activity=activity)
        registration.states.accept(save=True)
        mail.outbox = []

        for n in range(1, 20):
            day = start + timedelta(days=n)
            self.run_task(day)
            if n == 3:
                self.assertEqual(activity.slots.count(), 4)
                self.assertEqual(registration.participants.count(), 4)
                self.assertEqual(len(mail.outbox), 0)
            if n == 4:
                self.assertEqual(activity.slots.count(), 5)
                self.assertEqual(registration.participants.count(), 5)
                self.assertEqual(len(mail.outbox), 0)
            if n == 5:
                self.assertEqual(activity.slots.count(), 6)
                self.assertEqual(registration.participants.count(), 6)
                self.assertEqual(len(mail.outbox), 1)
                self.assertHasMail('⏰ Reminder: Update your participation!')
            elif n == 6:
                self.assertEqual(len(mail.outbox), 2)
            elif n == 10:
                self.assertEqual(len(mail.outbox), 6)
            elif n == 13:
                self.assertEqual(len(mail.outbox), 9)
                registration.states.stop(save=True)
                self.assertEqual(len(mail.outbox), 11)
                self.assertHasMail('Your contribution to the activity "A nice time" has been stopped')
                self.assertHasMail('A participant for your activity "A nice time" has stopped')
            elif n == 16:
                self.assertEqual(len(mail.outbox), 11)
            elif n == 20:
                self.assertEqual(len(mail.outbox), 11)


class ScheduleSlotTestCase(BluebottleTestCase):

    def setUp(self):
        super(ScheduleSlotTestCase, self).setUp()
        self.initiative = InitiativeFactory.create(status="approved")

        self.slot = ScheduleSlotFactory.create(
            start=now() + timedelta(days=5), duration=timedelta(hours=5)
        )
        self.participant = ScheduleParticipantFactory.create(
            activity=self.slot.activity
        )
        self.participant.slot = self.slot
        self.participant.save()
        self.participant.refresh_from_db()

    def run_task(self, when):
        with mock.patch.object(timezone, "now", return_value=when):
            schedule_slot_tasks()

        with LocalTenant(connection.tenant, clear_tenant=True):
            self.slot.refresh_from_db()
            self.participant.refresh_from_db()

    @property
    def before(self):
        return self.slot.start - timedelta(days=1)

    @property
    def started(self):
        return self.slot.start + timedelta(hours=1)

    @property
    def finished(self):
        return self.slot.end + timedelta(hours=1)

    def test_before(self):
        self.run_task(self.before)
        self.assertEqual(self.slot.status, "new")
        self.assertEqual(self.participant.status, "scheduled")

    def test_during(self):
        self.run_task(self.started)
        self.assertEqual(self.slot.status, "running")
        self.assertEqual(self.participant.status, "scheduled")

    def test_after(self):
        self.run_task(self.finished)
        self.assertEqual(self.slot.status, "finished")
        self.assertEqual(self.participant.status, "succeeded")


class TeamScheduleSlotTestCase(BluebottleTestCase):

    def setUp(self):
        super(TeamScheduleSlotTestCase, self).setUp()
        self.initiative = InitiativeFactory.create(status="approved")

        self.activity = ScheduleActivityFactory.create(
            initiative=self.initiative, team_activity="teams"
        )
        self.activity.states.publish(save=True)

        self.team = TeamFactory.create(activity=self.activity)
        self.slot = self.team.slots.first()

        self.slot.start = now() + timedelta(days=5)
        self.slot.duration = timedelta(hours=5)
        self.slot.save()

        self.team_member = TeamMemberFactory.create(team=self.team)
        self.participant = self.team_member.participants.first()

    def run_task(self, when):
        with mock.patch.object(timezone, "now", return_value=when):
            team_schedule_slot_tasks()

        with LocalTenant(connection.tenant, clear_tenant=True):
            self.slot.refresh_from_db()
            self.participant.refresh_from_db()

    @property
    def before(self):
        return self.slot.start - timedelta(days=1)

    @property
    def started(self):
        return self.slot.start + timedelta(hours=1)

    @property
    def finished(self):
        return self.slot.end + timedelta(hours=1)

    def test_before(self):
        self.run_task(self.before)
        self.assertEqual(self.slot.status, "scheduled")
        self.assertEqual(self.participant.status, "scheduled")

    def test_during(self):
        self.run_task(self.started)
        self.assertEqual(self.slot.status, "running")
        self.assertEqual(self.participant.status, "scheduled")

    def test_after(self):
        self.run_task(self.finished)
        self.assertEqual(self.slot.status, "finished")
        self.assertEqual(self.participant.status, "succeeded")


class ScheduleActivityTestCase(BluebottleTestCase):
    def setUp(self):
        super(ScheduleActivityTestCase, self).setUp()
        self.initiative = InitiativeFactory.create(status="approved")
        self.deadline = now() + timedelta(days=4)

        self.activity = ScheduleActivityFactory.create(
            initiative=self.initiative,
            team_activity="teams",
            registration_deadline=None,
            review=False,
            deadline=self.deadline.date(),
        )
        self.activity.states.publish(save=True)

        self.team = TeamFactory.create(activity=self.activity)

        self.slot = self.team.slots.first()
        self.slot.start = now() + timedelta(days=5)
        self.slot.duration = timedelta(hours=5)
        self.slot.save()

        self.team_member = TeamMemberFactory.create(team=self.team)
        self.participant = self.team_member.participants.first()

    def run_task(self, when):
        with mock.patch.object(timezone, "now", return_value=when):
            with mock.patch("bluebottle.time_based.periodic_tasks.date") as mock_date:
                mock_date.today.return_value = when.date()
                mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
                schedule_activity_tasks()

        with LocalTenant(connection.tenant, clear_tenant=True):
            self.activity.refresh_from_db()
            self.team.refresh_from_db()
            self.team_member.refresh_from_db()
            self.participant.refresh_from_db()

    @property
    def before(self):
        return self.deadline - timedelta(days=4)

    @property
    def finished(self):
        return self.deadline + timedelta(days=1)

    def test_before(self):
        self.run_task(self.before)
        self.assertEqual(self.activity.status, "open")
        self.assertEqual(self.participant.status, "scheduled")
        self.assertEqual(self.participant.contributions.get().status, "new")

    def test_after(self):
        self.run_task(self.finished)
        self.assertEqual(self.activity.status, "succeeded")
        self.assertEqual(self.participant.status, "scheduled")
        self.assertEqual(self.participant.contributions.get().status, "succeeded")
