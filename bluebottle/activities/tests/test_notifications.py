from bluebottle.activities.messages import (
    ActivityRejectedNotification, ActivityCancelledNotification,
    ActivitySucceededNotification, ActivityRestoredNotification,
    ActivityExpiredNotification, TeamAddedMessage,
    TeamAppliedMessage, TeamAcceptedMessage, TeamCancelledMessage,
    TeamCancelledTeamCaptainMessage, TeamWithdrawnActivityOwnerMessage,
    TeamWithdrawnMessage
)
from bluebottle.activities.tests.factories import TeamFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import NotificationTestCase
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, PeriodActivityFactory, PeriodParticipantFactory
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
            title="Save the world!"
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
        self.assertTextBodyContains("William Shatner's team has joined your activity \"Save the world!\".")
        self.assertBodyContains('Please contact them to sort out any details via kirk@enterprise.com.')
        self.assertActionLink(self.obj.activity.get_absolute_url())
        self.assertActionTitle('View activity')

    def test_team_applied_notification(self):
        self.activity.review = True
        self.activity.save()
        self.message_class = TeamAppliedMessage
        self.create()
        self.assertRecipients([self.activity.owner])
        self.assertSubject("A new team has applied to \"Save the world!\"")
        self.assertTextBodyContains("William Shatner's team has applied to your activity \"Save the world!\".")
        self.assertBodyContains('Please contact them to sort out any details via kirk@enterprise.com.')
        self.assertBodyContains('You can accept or reject the team on the activity page.')

        self.assertActionLink(self.obj.activity.get_absolute_url())
        self.assertActionTitle('View activity')

    def test_team_accepted_notification(self):
        self.activity.review = True
        self.activity.save()
        self.message_class = TeamAcceptedMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject("Your team has been accepted for \"Save the world!\"")
        self.assertBodyContains('On the activity page you will find the link to invite your team members.')

    def test_team_cancelled_notification(self):
        PeriodParticipantFactory.create_batch(10, activity=self.activity, team=self.obj)

        self.message_class = TeamCancelledMessage
        self.create()
        self.assertRecipients([participant.user for participant in self.obj.members.all()])
        self.assertSubject("Team cancellation for 'Save the world!'")
        self.assertHtmlBodyContains(
            "Your team 'William Shatner&#39;s team' is no longer participating in the activity 'Save the world!'."
        )

        self.assertActionLink(self.obj.activity.get_absolute_url())
        self.assertActionTitle('View activity')

    def test_team_cancelled_team_captain_notification(self):
        self.message_class = TeamCancelledTeamCaptainMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject("Your team has been rejected for 'Save the world!'")
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
            "Your team 'William Shatner&#39;s team' is no longer participating in the activity 'Save the world!'."
        )

        self.assertActionLink(self.obj.activity.get_absolute_url())
        self.assertActionTitle('View activity')

    def test_team_withdrawn_activity_manager_notification(self):
        self.message_class = TeamWithdrawnActivityOwnerMessage
        self.create()
        self.assertRecipients([self.activity.owner])
        self.assertSubject("Team cancellation for 'Save the world!'")
        self.assertHtmlBodyContains(
            "William Shatner&#39;s team has cancelled its participation in your activity 'Save the world!'."
        )

        self.assertActionLink(self.obj.activity.get_absolute_url())
        self.assertActionTitle('View activity')
