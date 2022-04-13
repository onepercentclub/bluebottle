from bluebottle.activities.messages import ActivityRejectedNotification, ActivityCancelledNotification, \
    ActivitySucceededNotification, ActivityRestoredNotification, ActivityExpiredNotification, TeamAddedMessage
from bluebottle.activities.tests.factories import TeamFactory
from bluebottle.test.utils import NotificationTestCase

from bluebottle.time_based.tests.factories import DateActivityFactory, PeriodActivityFactory
from build.lib.bluebottle.test.factory_models.accounts import BlueBottleUserFactory


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
        self.assertSubject("A new team has joined 'Save the world!'")
        self.assertTextBodyContains("William Shatner's team has joined your activity 'Save the world!'.")
        self.assertBodyContains('Please contact them to sort out any details via kirk@enterprise.com.')
        self.assertActionLink(self.obj.activity.get_absolute_url())
        self.assertActionTitle('Open your activity')
