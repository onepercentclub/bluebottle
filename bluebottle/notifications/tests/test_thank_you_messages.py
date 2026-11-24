import json
from datetime import date, timedelta

import mock
from django.contrib.admin import site
from django.core import mail
from django.db import connection
from django.utils.timezone import now

from bluebottle.clients.utils import LocalTenant
from bluebottle.collect.models import CollectActivity
from bluebottle.collect.tasks import collect_tasks
from bluebottle.collect.tests.factories import CollectActivityFactory, CollectContributorFactory
from bluebottle.deeds.models import Deed
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.initiatives.tests.factories import (
    InitiativeFactory,
    InitiativePlatformSettingsFactory,
)
from bluebottle.notifications.models import ActivityMessageTemplate
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.models import (
    DateActivity,
    DeadlineActivity,
    PeriodicActivity,
    RegisteredDateActivity,
    ScheduleActivity,
)
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DateParticipantFactory,
    DateRegistrationFactory,
    DeadlineActivityFactory,
    DeadlineRegistrationFactory,
    PeriodicActivityFactory,
    PeriodicRegistrationFactory,
    ScheduleActivityFactory,
    ScheduleParticipantFactory,
    ScheduleSlotFactory,
    TeamFactory,
    TeamMemberFactory,
    TeamScheduleRegistrationFactory,
)


class ThankYouTestCase(BluebottleTestCase):
    activity_type = None

    def setUp(self):
        super().setUp()
        InitiativePlatformSettingsFactory.create(activity_types=[self.activity_type])
        self.owner = BlueBottleUserFactory.create()
        self.initiative = InitiativeFactory.create(owner=self.owner)
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.user = BlueBottleUserFactory.create(first_name='Henk')

    def publish(self, activity):
        activity.states.publish(save=True)
        return activity

    def thank_you_mails(self, user=None):
        user = user or self.user
        return [
            message for message in mail.outbox
            if message.to == [user.email] and message.subject.startswith('Thank you for participating')
        ]

    def disable(self):
        self.activity.send_thank_you_message = False
        self.activity.save()

    def add_template(self, activity):
        ActivityMessageTemplate.objects.create(
            activity=activity,
            action='succeed',
            body_html=json.dumps({'html': '<p>Drinks are on us!</p>', 'delta': ''}),
        )


class SharedThankYouTests:
    def succeed(self):
        raise NotImplementedError

    def test_on_by_default(self):
        self.assertTrue(self.activity.send_thank_you_message)

    def test_sent(self):
        self.succeed()

        message = self.thank_you_mails()[0]
        self.assertIn('Thank you for participating in an activity on', message.body)

    def test_not_sent_when_disabled(self):
        self.disable()
        self.succeed()

        self.assertEqual(len(self.thank_you_mails()), 0)

    def test_owner_not_thanked(self):
        self.succeed()

        self.assertEqual(len(self.thank_you_mails(self.owner)), 0)


class DeadlineThankYouTestCase(SharedThankYouTests, ThankYouTestCase):
    activity_type = 'deadlineactivity'

    def setUp(self):
        super().setUp()
        self.activity = self.publish(DeadlineActivityFactory.create(
            initiative=self.initiative, owner=self.owner, review=False,
            registration_deadline=None,
            start=date.today() - timedelta(days=5),
            deadline=date.today() + timedelta(days=5),
        ))
        DeadlineRegistrationFactory.create(activity=self.activity, user=self.user, as_user=self.user)
        mail.outbox = []

    def succeed(self):
        self.activity.states.succeed_manually(save=True)

    def test_succeed_manually(self):
        self.activity.states.succeed_manually(save=True)

        message = self.thank_you_mails()[0]
        self.assertEqual(
            message.subject,
            'Thank you for participating in the activity "{}"'.format(self.activity.title)
        )
        self.assertIn('Thank you for participating in an activity on', message.body)
        self.assertIn(self.activity.title, message.body)

    def test_deadline_passed(self):
        self.activity.deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'succeeded')
        self.assertEqual(len(self.thank_you_mails()), 1)

    def test_activity_template_is_appended(self):
        self.add_template(self.activity)
        self.activity.states.succeed_manually(save=True)

        message = self.thank_you_mails()[0]
        self.assertIn('Thank you for participating in an activity on', message.body)
        self.assertIn('Drinks are on us!', message.body)

    def test_withdrawn_participant_not_thanked(self):
        registration = self.activity.registrations.get()
        participant = registration.participants.get()
        participant.states.withdraw(save=True)
        other = BlueBottleUserFactory.create()
        DeadlineRegistrationFactory.create(activity=self.activity, user=other, as_user=other)
        mail.outbox = []

        self.activity.states.succeed_manually(save=True)

        self.assertEqual(len(self.thank_you_mails(other)), 1)
        self.assertEqual(len(self.thank_you_mails()), 0)


class PeriodicThankYouTestCase(SharedThankYouTests, ThankYouTestCase):
    activity_type = 'periodicactivity'

    def setUp(self):
        super().setUp()
        self.activity = self.publish(PeriodicActivityFactory.create(
            initiative=self.initiative, owner=self.owner, review=False,
            registration_deadline=None,
            start=date.today() - timedelta(days=14),
            deadline=date.today() + timedelta(days=14),
        ))
        self.registration = PeriodicRegistrationFactory.create(
            activity=self.activity, user=self.user, as_user=self.user
        )
        mail.outbox = []

    def start_slot(self):
        slot = self.activity.slots.get()
        slot.states.start(save=True)
        return slot

    def finish_slot(self, slot=None):
        slot = slot or self.start_slot()
        slot.states.finish(save=True)
        mail.outbox = []

    def succeed(self):
        self.finish_slot()
        self.activity.states.succeed_manually(save=True)

    def test_deadline_passed(self):
        self.finish_slot()
        self.activity.deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'succeeded')
        self.assertEqual(len(self.thank_you_mails()), 1)

    def test_stopped_participant_thanked(self):
        self.finish_slot()
        self.registration.states.stop(save=True)

        self.activity.states.succeed_manually(save=True)

        self.assertEqual(len(self.thank_you_mails()), 1)

    def test_removed_participant_not_thanked(self):
        slot = self.start_slot()
        for participant in self.registration.participants.all():
            participant.states.remove(save=True)
        self.finish_slot(slot)

        self.activity.states.succeed_manually(save=True)

        self.assertEqual(len(self.thank_you_mails()), 0)

    def test_no_succeeded_contribution_not_thanked(self):
        self.activity.states.succeed_manually(save=True)

        self.assertEqual(len(self.thank_you_mails()), 0)


class DateThankYouTestCase(SharedThankYouTests, ThankYouTestCase):
    activity_type = 'dateactivity'

    def setUp(self):
        super().setUp()
        self.activity = DateActivityFactory.create(
            initiative=self.initiative, owner=self.owner, review=False,
            registration_deadline=None, slots=[],
        )
        self.slot = DateActivitySlotFactory.create(
            activity=self.activity, start=now() + timedelta(days=2)
        )
        self.publish(self.activity)
        registration = DateRegistrationFactory.create(
            activity=self.activity, user=self.user, as_user=self.user
        )
        self.participant = DateParticipantFactory.create(
            registration=registration, slot=self.slot, as_user=self.user
        )
        mail.outbox = []

    def finish(self, slot):
        slot.start = now() - timedelta(days=2)
        slot.save()

    def succeed(self):
        self.finish(self.slot)

    def test_slot_finished(self):
        self.finish(self.slot)

        self.participant.refresh_from_db()
        self.assertEqual(self.participant.status, 'succeeded')
        message = self.thank_you_mails()[0]
        self.assertIn('Thank you for participating in an activity on', message.body)

    def test_each_slot_thanks_once(self):
        second_slot = DateActivitySlotFactory.create(
            activity=self.activity, start=now() + timedelta(days=4)
        )
        DateParticipantFactory.create(
            registration=self.participant.registration, slot=second_slot, as_user=self.user
        )
        mail.outbox = []

        self.finish(self.slot)
        self.assertEqual(len(self.thank_you_mails()), 1)

        self.finish(second_slot)
        self.assertEqual(len(self.thank_you_mails()), 2)

    def test_slot_details_in_mail(self):
        self.slot.title = 'Morning shift'
        self.slot.save()
        self.finish(self.slot)

        message = self.thank_you_mails()[0]
        self.assertIn('Morning shift', message.body)
        self.assertIn('slot-info', message.alternatives[0][0])

    def test_each_mail_shows_own_slot(self):
        self.slot.title = 'First slot'
        self.slot.save()
        second_slot = DateActivitySlotFactory.create(
            activity=self.activity, start=now() + timedelta(days=4), title='Second slot'
        )
        DateParticipantFactory.create(
            registration=self.participant.registration, slot=second_slot, as_user=self.user
        )
        mail.outbox = []

        self.finish(self.slot)
        self.finish(second_slot)

        first, second = self.thank_you_mails()
        self.assertIn('First slot', first.body)
        self.assertNotIn('Second slot', first.body)
        self.assertIn('Second slot', second.body)
        self.assertNotIn('First slot', second.body)

    def test_send_once(self):
        self.finish(self.slot)
        self.slot.start = now() + timedelta(days=2)
        self.slot.save()
        self.finish(self.slot)

        self.assertEqual(len(self.thank_you_mails()), 1)


class ScheduleThankYouTestCase(SharedThankYouTests, ThankYouTestCase):
    activity_type = 'scheduleactivity'

    def setUp(self):
        super().setUp()
        self.activity = self.publish(ScheduleActivityFactory.create(
            initiative=self.initiative, owner=self.owner, review=False,
            registration_deadline=None,
        ))
        self.participant = ScheduleParticipantFactory.create(activity=self.activity, user=self.user)
        mail.outbox = []

    def succeed(self):
        slot = ScheduleSlotFactory.create(activity=self.activity, start=now() + timedelta(days=2))
        self.participant.slot = slot
        self.participant.save()

        slot.start = now() - timedelta(days=2)
        slot.save()

    def test_unscheduled_not_thanked(self):
        self.activity.states.succeed_manually(save=True)

        self.assertEqual(len(self.thank_you_mails()), 0)


class TeamScheduleThankYouTestCase(SharedThankYouTests, ThankYouTestCase):
    activity_type = 'scheduleactivity'

    def setUp(self):
        super().setUp()
        self.activity = self.publish(ScheduleActivityFactory.create(
            initiative=self.initiative, owner=self.owner, review=False,
            registration_deadline=None, team_activity='teams',
        ))
        self.team = self.create_team()
        mail.outbox = []

    def create_team(self):
        registration = TeamScheduleRegistrationFactory.create(activity=self.activity, user=self.user)
        return TeamFactory.create(registration=registration, activity=self.activity, user=self.user)

    def finish(self, team):
        slot = team.slots.first()
        slot.start = now() - timedelta(days=2)
        slot.save()

    def succeed(self):
        self.finish(self.team)

    def test_team_members_not_thanked(self):
        members = TeamMemberFactory.create_batch(2, team=self.team)
        mail.outbox = []

        self.finish(self.team)

        self.assertEqual(len(self.thank_you_mails()), 1)
        for member in members:
            self.assertEqual(len(self.thank_you_mails(member.user)), 0)

    def test_captain_of_two_teams(self):
        other_team = self.create_team()
        mail.outbox = []

        self.finish(self.team)
        self.finish(other_team)

        self.assertEqual(len(self.thank_you_mails()), 2)


class DeedThankYouTestCase(SharedThankYouTests, ThankYouTestCase):
    activity_type = 'deed'

    def setUp(self):
        super().setUp()
        self.activity = self.publish(DeedFactory.create(
            initiative=self.initiative, owner=self.owner,
            start=date.today() - timedelta(days=5), end=None,
        ))
        DeedParticipantFactory.create(activity=self.activity, user=self.user)
        mail.outbox = []

    def succeed(self):
        self.activity.states.succeed_manually(save=True)

    def test_end_passed(self):
        self.activity.end = date.today() - timedelta(days=1)
        self.activity.save()

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'succeeded')
        self.assertEqual(len(self.thank_you_mails()), 1)

    def test_send_once(self):
        self.activity.states.succeed_manually(save=True)
        self.activity.states.reopen(save=True)
        self.activity.states.succeed_manually(save=True)

        self.assertEqual(len(self.thank_you_mails()), 1)


class CollectThankYouTestCase(SharedThankYouTests, ThankYouTestCase):
    activity_type = 'collectactivity'

    def setUp(self):
        super().setUp()
        self.activity = self.publish(CollectActivityFactory.create(
            initiative=self.initiative, owner=self.owner,
            start=date.today() - timedelta(days=5), end=None,
        ))
        CollectContributorFactory.create(activity=self.activity, user=self.user)
        mail.outbox = []

    def succeed(self):
        self.activity.states.succeed_manually(save=True)

    def test_end_passed(self):
        self.activity.end = date.today() - timedelta(days=1)
        self.activity.save()

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'succeeded')
        self.assertEqual(len(self.thank_you_mails()), 1)


class CollectEndDateThankYouTestCase(ThankYouTestCase):
    activity_type = 'collectactivity'

    def setUp(self):
        super().setUp()
        self.activity = self.publish(CollectActivityFactory.create(
            initiative=self.initiative, owner=self.owner,
            start=date.today(), end=date.today() + timedelta(days=10),
        ))
        self.contributor = CollectContributorFactory.create(activity=self.activity, user=self.user)
        self.contributor.refresh_from_db()
        mail.outbox = []

    def run_tasks(self, when):
        with mock.patch('bluebottle.collect.periodic_tasks.date') as periodic_date, \
                mock.patch('bluebottle.collect.triggers.date') as trigger_date:
            for mock_date in (periodic_date, trigger_date):
                mock_date.today.return_value = when
                mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            collect_tasks()

        with LocalTenant(connection.tenant, clear_tenant=True):
            self.activity.refresh_from_db()
            self.contributor.refresh_from_db()

    def test_participant_waits_for_end_date(self):
        self.assertEqual(self.contributor.status, 'accepted')

    def test_end_moved_into_the_past(self):
        self.activity.end = date.today() - timedelta(days=1)
        self.activity.save()

        self.activity.refresh_from_db()
        self.contributor.refresh_from_db()
        self.assertEqual(self.activity.status, 'succeeded')
        self.assertEqual(self.contributor.status, 'succeeded')
        self.assertEqual(len(self.thank_you_mails()), 1)

    def test_end_moved_into_the_past_custom_message(self):
        self.add_template(self.activity)
        self.activity.end = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(len(self.thank_you_mails()), 1)
        self.assertIn('Drinks are on us!', self.thank_you_mails()[0].body)

    def test_end_moved_into_the_past_disabled(self):
        self.disable()
        self.activity.end = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(len(self.thank_you_mails()), 0)

    def test_periodic_task(self):
        self.run_tasks(self.activity.end + timedelta(days=1))

        self.assertEqual(self.activity.status, 'succeeded')
        self.assertEqual(self.contributor.status, 'succeeded')
        self.assertEqual(len(self.thank_you_mails()), 1)

    def test_periodic_task_custom_message(self):
        self.add_template(self.activity)
        self.run_tasks(self.activity.end + timedelta(days=1))

        self.assertIn('Drinks are on us!', self.thank_you_mails()[0].body)

    def test_periodic_task_withdrawn_participant_not_thanked(self):
        self.contributor.states.withdraw(save=True)
        other = BlueBottleUserFactory.create()
        CollectContributorFactory.create(activity=self.activity, user=other)
        mail.outbox = []

        self.run_tasks(self.activity.end + timedelta(days=1))

        self.assertEqual(len(self.thank_you_mails()), 0)
        self.assertEqual(len(self.thank_you_mails(other)), 1)

    def test_periodic_task_thanks_once(self):
        self.run_tasks(self.activity.end + timedelta(days=1))
        self.run_tasks(self.activity.end + timedelta(days=2))

        self.assertEqual(len(self.thank_you_mails()), 1)


class ThankYouAdminTestCase(BluebottleTestCase):
    def registration_fields(self, model):
        return site._registry[model].get_registration_fields(None, None)

    def test_field_shown_for_activities_with_thank_you(self):
        for model in (
            CollectActivity, Deed, DateActivity, DeadlineActivity, PeriodicActivity, ScheduleActivity
        ):
            self.assertIn('send_thank_you_message', self.registration_fields(model))

    def test_field_not_shown_for_other_activities(self):
        self.assertNotIn('send_thank_you_message', self.registration_fields(RegisteredDateActivity) or [])
