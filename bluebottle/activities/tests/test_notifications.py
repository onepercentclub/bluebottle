from datetime import timedelta

from django.utils.timezone import now

from bluebottle.activities.messages import (
    ActivityRejectedNotification, ActivityCancelledNotification,
    ActivitySucceededNotification, ActivityRestoredNotification,
    ActivityExpiredNotification, TeamAddedMessage,
    TeamAppliedMessage, TeamCancelledMessage,
    TeamCancelledTeamCaptainMessage, TeamWithdrawnActivityOwnerMessage,
    TeamWithdrawnMessage, TeamMemberAddedMessage, TeamMemberWithdrewMessage,
    TeamMemberRemovedMessage, TeamReappliedMessage, TeamCaptainAcceptedMessage, DoGoodHoursReminderQ1Notification,
    DoGoodHoursReminderQ3Notification, DoGoodHoursReminderQ2Notification, DoGoodHoursReminderQ4Notification
)
from bluebottle.activities.tests.factories import TeamFactory
from bluebottle.members.models import MemberPlatformSettings, Member
from bluebottle.notifications.models import NotificationPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import NotificationTestCase
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, PeriodActivityFactory, PeriodParticipantFactory, DateActivitySlotFactory,
    DateParticipantFactory, SlotParticipantFactory
)


class ActivityNotificationTestCase(NotificationTestCase):

    def setUp(self):
        self.obj = DateActivityFactory.create(
            title="Save the world!"
        )

    def test_activity_rejected_notification(self):
        self.message_class = ActivityRejectedNotification
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your activity "Save the world!" has been rejected')
        self.assertBodyContains('Unfortunately your activity "Save the world!" has been rejected.')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('Open your activity')

    def test_activity_cancelled_notification(self):
        self.message_class = ActivityCancelledNotification
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your activity "Save the world!" has been cancelled')
        self.assertBodyContains('Unfortunately your activity "Save the world!" has been cancelled.')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('Open your activity')

    def test_activity_restored_notification(self):
        self.message_class = ActivityRestoredNotification
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('The activity "Save the world!" has been restored')
        self.assertBodyContains('Your activity "Save the world!" has been restored.')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('Open your activity')

    def test_activity_expired_notification(self):
        self.message_class = ActivityExpiredNotification
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('The registration deadline for your activity "Save the world!" has expired')
        self.assertBodyContains(
            'Unfortunately, nobody applied to your activity '
            '"Save the world!" before the deadline to apply. '
            'That’s why we have cancelled your activity.')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('Open your activity')

    def test_activity_succeeded_notification(self):
        self.message_class = ActivitySucceededNotification
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your activity "Save the world!" has succeeded 🎉')
        self.assertBodyContains(
            'You did it! Your activity "Save the world!" has succeeded, '
            'that calls for a celebration!')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('Open your activity')


class TeamNotificationTestCase(NotificationTestCase):

    def setUp(self):
        self.activity = PeriodActivityFactory.create(
            title="Save the world!",
            team_activity='teams'
        )
        self.captain = BlueBottleUserFactory.create(
            first_name='William',
            last_name='Shatner',
            email='kirk@enterprise.com',
            username='shatner'
        )
        self.obj = TeamFactory.create(
            activity=self.activity,
            owner=self.captain
        )

    def test_team_added_notification(self):
        self.message_class = TeamAddedMessage
        self.create()
        self.assertRecipients([self.activity.owner])
        self.assertSubject("A new team has joined \"Save the world!\"")
        self.assertTextBodyContains("Team William Shatner has joined your activity \"Save the world!\".")
        self.assertBodyContains(
            'Add this information to the team via the unscheduled team list on the activity '
            'page so it is visible for the team members.'
        )
        self.assertActionLink(self.obj.activity.get_absolute_url())
        self.assertActionTitle('View activity')

    def test_team_applied_notification(self):
        self.activity.review = True
        self.activity.save()
        self.message_class = TeamAppliedMessage
        self.create()
        self.assertRecipients([self.activity.owner])
        self.assertSubject("A new team has applied to \"Save the world!\"")
        self.assertTextBodyContains("Team William Shatner has applied to your activity \"Save the world!\".")
        self.assertBodyContains(
            'Add this information to the team via the unscheduled team list on the activity '
            'page so it is visible for the team members.'
        )

        self.assertActionLink(self.obj.activity.get_absolute_url())
        self.assertActionTitle('View activity')

    def test_team_accepted_notification(self):
        self.obj = PeriodParticipantFactory.create(
            user=self.captain,
            activity=self.activity,
            team=self.obj
        )
        self.activity.review = True
        self.activity.save()
        self.message_class = TeamCaptainAcceptedMessage
        self.create()
        self.assertRecipients([self.obj.user])
        self.assertSubject("Your team has been accepted for \"Save the world!\"")
        self.assertBodyContains('On the activity page you will find the link to invite your team members.')
        self.assertBodyContains(f"Your team has been accepted for the activity '{self.activity.title}'.")

    def test_team_cancelled_notification(self):
        PeriodParticipantFactory.create_batch(10, activity=self.activity, team=self.obj)

        self.message_class = TeamCancelledMessage
        self.create()
        self.assertRecipients([participant.user for participant in self.obj.members.all()])
        self.assertSubject("Team cancellation for 'Save the world!'")
        self.assertHtmlBodyContains(
            "Your team 'Team William Shatner' is no longer participating in the activity 'Save the world!'."
        )

        self.assertActionLink(self.obj.activity.get_absolute_url())
        self.assertActionTitle('View activity')

    def test_team_cancelled_team_captain_notification(self):
        self.obj = PeriodParticipantFactory.create(
            user=self.captain,
            activity=self.activity,
            team=self.obj
        )
        self.message_class = TeamCancelledTeamCaptainMessage
        self.create()
        self.assertRecipients([self.obj.user])
        self.assertSubject('Your team has been rejected for "Save the world!"')
        self.assertHtmlBodyContains(
            "Unfortunately, your team has been rejected for the activity 'Save the world!'."
        )

        self.assertActionLink(self.obj.activity.get_absolute_url())
        self.assertActionTitle('View activity')

    def test_team_withdrawn_notification(self):
        PeriodParticipantFactory.create_batch(10, activity=self.activity, team=self.obj)

        self.message_class = TeamWithdrawnMessage
        self.create()
        self.assertRecipients([participant.user for participant in self.obj.members.all()])
        self.assertSubject("Team cancellation for 'Save the world!'")
        self.assertHtmlBodyContains(
            "Your team 'Team William Shatner' is no longer participating in the activity 'Save the world!'."
        )

        self.assertActionLink(self.obj.activity.get_absolute_url())
        self.assertActionTitle('View activity')

    def test_team_withdrawn_activity_manager_notification(self):
        self.message_class = TeamWithdrawnActivityOwnerMessage
        self.create()
        self.assertRecipients([self.activity.owner])
        self.assertSubject("Team cancellation for 'Save the world!'")
        self.assertHtmlBodyContains(
            "Team William Shatner has cancelled its participation in your activity 'Save the world!'."
        )

        self.assertActionLink(self.obj.activity.get_absolute_url())
        self.assertActionTitle('View activity')

    def test_team_reapplied_notification(self):
        PeriodParticipantFactory.create_batch(10, activity=self.activity, team=self.obj)

        self.message_class = TeamReappliedMessage
        self.create()
        self.assertRecipients(
            [participant.user for participant in self.obj.members.all()
                if participant.user != self.obj.owner]
        )
        self.assertSubject(f"You’re added to a team for '{self.activity.title}'")
        self.assertHtmlBodyContains(
            "You’re added to team ‘Team William Shatner’ for the activity ‘Save the world!’."
        )

        self.assertActionLink(self.obj.activity.get_absolute_url())
        self.assertActionTitle('View activity')

    def test_team_member_added_notification(self):
        team_captain = PeriodParticipantFactory.create(activity=self.activity, user=self.captain)

        self.obj = PeriodParticipantFactory.create(
            activity=self.activity, accepted_invite=team_captain.invite
        )
        self.message_class = TeamMemberAddedMessage
        self.create()
        self.assertRecipients([self.captain])
        self.assertSubject('Someone has joined your team for "Save the world!"')
        self.assertHtmlBodyContains(
            f"{self.obj.user.full_name} is now part of your team for the activity ‘Save the world!’."
        )

        self.assertActionLink(self.obj.activity.get_absolute_url())
        self.assertActionTitle('View activity')

    def test_team_member_withdrew_notification(self):
        team_captain = PeriodParticipantFactory.create(activity=self.activity, user=self.captain)

        self.obj = PeriodParticipantFactory.create(
            activity=self.activity, accepted_invite=team_captain.invite
        )
        self.message_class = TeamMemberWithdrewMessage
        self.create()
        self.assertRecipients([self.captain])
        self.assertSubject('A participant has withdrawn from your team for "Save the world!"')
        self.assertHtmlBodyContains(
            f"{self.obj.user.full_name} has withdrawn from your team for the activity ‘Save the world!’."
        )

        self.assertActionLink(self.obj.activity.get_absolute_url())
        self.assertActionTitle('View activity')

    def test_team_member_removed_notification(self):
        team_captain = PeriodParticipantFactory.create(activity=self.activity, user=self.captain)

        self.obj = PeriodParticipantFactory.create(
            activity=self.activity, accepted_invite=team_captain.invite
        )
        self.message_class = TeamMemberRemovedMessage
        self.create()
        self.assertRecipients([self.captain])
        self.assertSubject("Team member removed for ‘Save the world!’")
        self.assertHtmlBodyContains((
            f"{self.obj.user.full_name} has been removed from your team "
            "for the activity ‘Save the world!’ by the activity manager."
        ))

        self.assertActionLink(self.obj.activity.get_absolute_url())
        self.assertActionTitle('View activity')


class DoGoodHoursReminderNotificationTestCase(NotificationTestCase):

    def setUp(self):
        self.obj = NotificationPlatformSettings.load()
        self.obj = MemberPlatformSettings.load()
        self.obj.do_good_hours = 8
        self.obj.save()
        activity = DateActivityFactory.create(
            slots=[],
            slot_selection='free',
        )

        slot1 = DateActivitySlotFactory.create(
            start=now() - timedelta(days=2),
            duration=timedelta(hours=4),
            activity=activity
        )
        slot2 = DateActivitySlotFactory.create(
            start=now() - timedelta(days=1),
            duration=timedelta(hours=4),
            activity=activity
        )
        old_slot = DateActivitySlotFactory.create(
            start=now().replace(year=2011),
            duration=timedelta(hours=8),
            activity=activity
        )

        self.active_user = BlueBottleUserFactory.create(first_name='Active')
        part1 = DateParticipantFactory.create(
            user=self.active_user,
            activity=activity
        )
        SlotParticipantFactory.create(
            participant=part1,
            slot=slot1
        )
        SlotParticipantFactory.create(
            participant=part1,
            slot=slot2
        )
        self.moderate_user = BlueBottleUserFactory.create(first_name='Moderate')
        part2 = DateParticipantFactory.create(
            user=self.moderate_user,
            activity=activity
        )
        SlotParticipantFactory.create(
            participant=part2,
            slot=slot1
        )
        SlotParticipantFactory.create(
            participant=part2,
            slot=old_slot
        )
        self.passive_user = BlueBottleUserFactory.create(first_name='Passive')
        part3 = DateParticipantFactory.create(
            user=self.passive_user,
            activity=activity
        )

        SlotParticipantFactory.create(
            participant=part3,
            slot=old_slot
        )

        Member.objects.exclude(id__in=[
            self.active_user.id,
            self.passive_user.id,
            self.moderate_user.id,
        ]).update(receive_reminder_emails=False)

    def test_reminder_q1(self):
        self.message_class = DoGoodHoursReminderQ1Notification
        self.create()
        self.assertRecipients([self.moderate_user, self.passive_user])
        self.assertSubject("Are you ready to do good? Q1")
        self.assertBodyContains('First reminder')
        self.assertActionTitle('Find activities')

    def test_reminder_q2(self):
        self.message_class = DoGoodHoursReminderQ2Notification
        self.create()
        self.assertRecipients([self.moderate_user, self.passive_user])
        self.assertSubject("Are you ready to do good? Q2")
        self.assertBodyContains('Second reminder')
        self.assertActionTitle('Find activities')

    def test_reminder_q3(self):
        self.message_class = DoGoodHoursReminderQ3Notification
        self.create()
        self.assertRecipients([self.moderate_user, self.passive_user])
        self.assertSubject("Are you ready to do good? Q3")
        self.assertBodyContains('Third reminder')
        self.assertActionTitle('Find activities')

    def test_reminder_q4(self):
        self.message_class = DoGoodHoursReminderQ4Notification
        self.create()
        self.assertRecipients([self.moderate_user, self.passive_user])
        self.assertSubject("Are you ready to do good? Q4")
        self.assertBodyContains('Fourth reminder')
        self.assertActionTitle('Find activities')
