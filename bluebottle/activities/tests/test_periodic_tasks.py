from datetime import date, datetime, timedelta
from unittest import mock

from django.core import mail
from django.utils import timezone
from django.utils.timezone import now

from bluebottle.activities.tasks import do_good_hours_reminder
from bluebottle.members.models import MemberPlatformSettings, Member
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, DateActivitySlotFactory, DateParticipantFactory,
    SlotParticipantFactory
)


class DoGoodHoursReminderPeriodicTasksTest(BluebottleTestCase):

    def setUp(self):
        super().setUp()
        settings = MemberPlatformSettings.load()
        settings.do_good_hours = 8
        settings.reminder_q1 = True
        settings.reminder_q2 = True
        settings.reminder_q3 = False
        settings.reminder_q4 = True
        settings.save()

        activity = DateActivityFactory.create(
            slots=[],
            slot_selection='free',
        )

        self.slot1 = DateActivitySlotFactory.create(
            start=self.after_q1,
            duration=timedelta(hours=4),
            activity=activity
        )
        self.slot2 = DateActivitySlotFactory.create(
            start=self.after_q1,
            duration=timedelta(hours=4),
            activity=activity
        )
        self.slot3 = DateActivitySlotFactory.create(
            start=self.after_q2,
            duration=timedelta(hours=8),
            activity=activity
        )
        old_slot = DateActivitySlotFactory.create(
            start=now().replace(year=2011),
            duration=timedelta(hours=8),
            activity=activity
        )

        self.active_user = BlueBottleUserFactory.create(first_name='Active')
        self.part1 = DateParticipantFactory.create(
            user=self.active_user,
            activity=activity
        )
        SlotParticipantFactory.create(
            participant=self.part1,
            slot=self.slot1
        )
        SlotParticipantFactory.create(
            participant=self.part1,
            slot=self.slot2
        )
        self.moderate_user = BlueBottleUserFactory.create(first_name='Moderate')
        self.part2 = DateParticipantFactory.create(
            user=self.moderate_user,
            activity=activity
        )
        SlotParticipantFactory.create(
            participant=self.part2,
            slot=self.slot1
        )
        SlotParticipantFactory.create(
            participant=self.part2,
            slot=old_slot
        )

        self.tempted_user = BlueBottleUserFactory.create(first_name='Tempted')
        self.part3 = DateParticipantFactory.create(
            user=self.tempted_user,
            activity=activity
        )
        SlotParticipantFactory.create(
            participant=self.part3,
            slot=old_slot
        )

        self.passive_user = BlueBottleUserFactory.create(first_name='Passive')

        Member.objects.exclude(id__in=[
            self.active_user.id,
            self.passive_user.id,
            self.moderate_user.id,
            self.tempted_user.id,
        ]).update(receive_reminder_emails=False)

        mail.outbox = []

    def run_task(self, when):
        with mock.patch.object(timezone, 'now', return_value=when):
            with mock.patch('bluebottle.activities.tasks.date') as mock_date:
                mock_date.today.return_value = when.date()
                mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
                do_good_hours_reminder()

    @property
    def q1(self):
        return timezone.get_current_timezone().localize(
            datetime(2022, 1, 1)
        )

    @property
    def after_q1(self):
        return timezone.get_current_timezone().localize(
            datetime(now().year, 1, 12)
        )

    @property
    def after_q2(self):
        return timezone.get_current_timezone().localize(
            datetime(now().year, 4, 15)
        )

    @property
    def q2(self):
        return timezone.get_current_timezone().localize(
            datetime(now().year, 4, 1)
        )

    @property
    def q3(self):
        return timezone.get_current_timezone().localize(
            datetime(now().year, 7, 1)
        )

    @property
    def q4(self):
        return timezone.get_current_timezone().localize(
            datetime(now().year, 10, 1)
        )

    def test_reminder_q1(self):
        self.run_task(self.q1)
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(
            mail.outbox[0].subject,
            'Are you ready to do good? Q1'
        )
        recipients = [m.to[0] for m in mail.outbox]
        self.assertTrue(self.moderate_user.email in recipients, "Moderate user should receive email")
        self.assertTrue(self.passive_user.email in recipients, "Passive user should receive email")
        self.assertTrue(self.tempted_user.email in recipients, "Tempted user should receive email")

        mail.outbox = []
        self.run_task(self.q1)
        self.assertEqual(len(mail.outbox), 0, "Reminder mail should not be send again.")

    def test_reminder_after_q1(self):
        self.run_task(self.after_q1)
        self.assertEqual(len(mail.outbox), 0)

    def test_reminder_q2(self):
        SlotParticipantFactory.create(
            participant=self.part3,
            slot=self.slot3
        )
        self.run_task(self.q2)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            'Are you ready to do good? Q2'
        )
        recipients = [m.to[0] for m in mail.outbox]
        self.assertTrue(self.moderate_user.email in recipients, "Moderate user should receive email")
        self.assertTrue(self.passive_user.email in recipients, "Passive user should receive email")
        self.assertFalse(self.tempted_user.email in recipients, "Tempted user should not receive email")

    def test_reminder_q3(self):
        SlotParticipantFactory.create(
            participant=self.part3,
            slot=self.slot3
        )
        self.run_task(self.q3)
        self.assertEqual(len(mail.outbox), 0, 'Q3 mails should be disabled')

    def test_reminder_q4(self):
        SlotParticipantFactory.create(
            participant=self.part3,
            slot=self.slot3
        )
        self.part3.states.withdraw(save=True)
        mail.outbox = []
        self.run_task(self.q4)
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(
            mail.outbox[0].subject,
            'Are you ready to do good? Q4'
        )
        recipients = [m.to[0] for m in mail.outbox]
        self.assertTrue(self.moderate_user.email in recipients, "Moderate user should receive email")
        self.assertTrue(self.passive_user.email in recipients, "Passive user should receive email")
        self.assertTrue(self.tempted_user.email in recipients, "Tempted user should receive email, because withdrawn")
