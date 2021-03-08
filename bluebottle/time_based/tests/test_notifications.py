from bluebottle.activities.messages import ActivityRejectedNotification, ActivityCancelledNotification, \
    ActivitySucceededNotification, ActivityRestoredNotification, ActivityExpiredNotification
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import NotificationTestCase
from bluebottle.time_based.messages import ParticipantRemovedNotification, ParticipantFinishedNotification, \
    ParticipantWithdrewNotification, NewParticipantNotification, ParticipantAddedOwnerNotification, \
    ParticipantRemovedOwnerNotification
from bluebottle.time_based.tests.factories import DateActivityFactory, DateParticipantFactory, DateActivitySlotFactory


class DateActivityNotificationTestCase(NotificationTestCase):

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


class DateParticipantNotificationTestCase(NotificationTestCase):

    def setUp(self):
        self.supporter = BlueBottleUserFactory.create(
            first_name='Frans',
            last_name='Beckenbauer'
        )
        self.owner = BlueBottleUserFactory.create()
        self.activity = DateActivityFactory.create(
            title="Save the world!",
            owner=self.owner,
            slots=[]
        )
        self.slots = DateActivitySlotFactory.create_batch(
            3,
            activity=self.activity
        )
        self.obj = DateParticipantFactory.create(
            activity=self.activity,
            user=self.supporter
        )

    def test_new_participant_notification(self):
        self.message_class = NewParticipantNotification
        self.create()
        self.assertRecipients([self.owner])
        self.assertSubject('A new participant has joined your activity "Save the world!" 🎉')
        self.assertBodyContains('Frans Beckenbauer applied to your activity "Save the world!"')
        self.assertActionLink(self.activity.get_absolute_url())
        self.assertActionTitle('Open your activity')

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

    def test_participant_withdrew_notification(self):
        self.message_class = ParticipantWithdrewNotification
        self.create()
        self.assertRecipients([self.owner])
        self.assertSubject('A participant has withdrawn from your activity "Save the world!"')
        self.assertBodyContains('Frans Beckenbauer has withdrawn from you activity "Save the world!"')
        self.assertActionLink(self.activity.get_absolute_url())
        self.assertActionTitle('Open your activity')

    def test_participant_added_owner_notification(self):
        self.message_class = ParticipantAddedOwnerNotification
        self.create()
        self.assertRecipients([self.owner])
        self.assertSubject('A new participant was added to your activity "Save the world!" 🎉')
        self.assertBodyContains('Frans Beckenbauer was added to your activity "Save the world!"')
        self.assertActionLink(self.activity.get_absolute_url())
        self.assertActionTitle('Open your activity')

    def test_participant_removed_owner_notification(self):
        self.message_class = ParticipantRemovedOwnerNotification
        self.create()
        self.assertRecipients([self.owner])
        self.assertSubject('A new participant was removed from your activity "Save the world!" 🎉')
        self.assertBodyContains('Frans Beckenbauer was removed from your activity "Save the world!"')
        self.assertActionLink(self.activity.get_absolute_url())
        self.assertActionTitle('Open your activity')
