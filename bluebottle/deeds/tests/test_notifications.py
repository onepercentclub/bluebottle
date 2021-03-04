from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from bluebottle.activities.messages import ActivityRejectedNotification, ActivityCancelledNotification, \
    ActivitySucceededNotification, ActivityRestoredNotification, ActivityExpiredNotification
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.test.utils import NotificationTestCase
from bluebottle.time_based.messages import ParticipantRemovedNotification, ParticipantFinishedNotification


class DeedNotificationTestCase(NotificationTestCase):

    def setUp(self):
        self.obj = DeedFactory.create(
            title="Save the world!"
        )

    def test_activity_rejected_notification(self):
        self.message_class = ActivityRejectedNotification
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your activity "Save the world!" has been rejected')
        self.assertBodyContains('Unfortunately your activity "Save the world!" has been rejected.')
        self.assertActionLink(self.obj.get_absolute_url())

    def test_activity_cancelled_notification(self):
        self.message_class = ActivityCancelledNotification
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your activity "Save the world!" has been cancelled')
        self.assertBodyContains('Unfortunately your activity "Save the world!" has been cancelled.')
        self.assertActionLink(self.obj.get_absolute_url())

    def test_activity_restored_notification(self):
        self.message_class = ActivityRestoredNotification
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('The activity "Save the world!" has been restored')
        self.assertBodyContains('Your activity "Save the world!" has been restored.')
        self.assertActionLink(self.obj.get_absolute_url())

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

    def test_activity_succeeded_notification(self):
        self.message_class = ActivitySucceededNotification
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your activity "Save the world!" has succeeded 🎉')
        self.assertBodyContains(
            'You did it! Your activity "Save the world!" has succeeded, '
            'that calls for a celebration!')
        self.assertActionLink(self.obj.get_absolute_url())


class ParticipantNotificationTestCase(NotificationTestCase):

    def setUp(self):
        self.supporter = BlueBottleUserFactory.create()
        self.owner = BlueBottleUserFactory.create()
        self.activity = DeedFactory.create(
            title="Save the world!",
            owner=self.owner
        )
        self.obj = DeedParticipantFactory.create(
            activity=self.activity,
            user=self.supporter
        )

    def test_participant_removed_notification(self):
        self.message_class = ParticipantRemovedNotification
        self.create()
        self.assertRecipients([self.supporter])
        self.assertSubject('You have been removed as participant for the activity "Save the world!"')
        self.assertBodyContains('You have been removed as participant for the activity "Save the world!"')
        self.assertActionLink('https://testserver/initiatives/activities/list')
        self.assertActionTitle('View all activities')

    def test_participant_finished_notification(self):
        self.message_class = ParticipantFinishedNotification
        self.create()
        self.assertRecipients([self.supporter])
        self.assertSubject('Your contribution to the activity "Save the world!" is successful 🎉')
        self.assertBodyContains('Congratulations! Your contribution to the activity "Save the world!" is finished.')
        self.assertActionLink(self.activity.get_absolute_url())
        self.assertActionTitle('View activity')
