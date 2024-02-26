from datetime import timedelta

from django.utils.timezone import now

from bluebottle.activities.messages import ActivityRejectedNotification, ActivityCancelledNotification, \
    ActivitySucceededNotification, ActivityRestoredNotification, ActivityExpiredNotification
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import NotificationTestCase
from bluebottle.time_based.messages import (
    ParticipantRemovedNotification, ParticipantFinishedNotification,
    ParticipantWithdrewNotification, NewParticipantNotification, ManagerParticipantAddedOwnerNotification,
    ParticipantRemovedOwnerNotification, ParticipantJoinedNotification, ParticipantAppliedNotification,
    SlotCancelledNotification, ParticipantAddedNotification, 
    ParticipantSlotParticipantRegisteredNotification,
    ManagerSlotParticipantRegisteredNotification, ParticipantCreatedNotification
)
from bluebottle.time_based.notifications.registrations import ManagerRegistrationCreatedNotification, \
    ManagerRegistrationCreatedReviewNotification
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, DateParticipantFactory,
    DateActivitySlotFactory, PeriodActivityFactory, PeriodParticipantFactory,
    SlotParticipantFactory, DeadlineActivityFactory, DeadlineRegistrationFactory
)


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

    def test_participant_registered_notification(self):
        self.obj = self.obj.slot_participants.first()
        self.message_class = ParticipantSlotParticipantRegisteredNotification
        self.create()
        self.assertRecipients([self.supporter])
        self.assertSubject('You\'ve registered for a time slot for the activity "Save the world!"')
        self.assertBodyContains('You are registered for a time slot for the activity')
        self.assertActionLink(self.obj.slot.get_absolute_url())
        self.assertActionTitle('View activity')

    def test_participant_registered_manager(self):
        self.activity.review_title = 'What is your favorite color?'
        self.activity.save()
        self.obj.motivation = 'Par-bleu yellow'
        self.obj.save()
        self.obj = self.obj.slot_participants.first()
        self.message_class = ManagerSlotParticipantRegisteredNotification
        self.create()
        self.assertRecipients([self.activity.owner])
        self.assertSubject('A participant has registered for a time slot for your activity "Save the world!"')
        self.assertBodyContains('has registered for a time slot for your activity')
        self.assertBodyContains('What is your favorite color?')
        self.assertBodyContains('Par-bleu yellow')

    def test_new_participant_notification(self):
        self.activity.review_title = 'What is your favorite color?'
        self.activity.save()
        self.obj.motivation = 'Par-bleu yellow'
        self.message_class = NewParticipantNotification
        self.create()
        self.assertRecipients([self.owner])
        self.assertSubject('A new participant has joined your activity "Save the world!" 🎉')
        self.assertBodyContains('Frans Beckenbauer has joined your activity "Save the world!"')
        self.assertActionLink(self.activity.get_absolute_url())
        self.assertActionTitle('Open your activity')
        self.assertBodyContains('What is your favorite color?')
        self.assertBodyContains('Par-bleu yellow')

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
        self.message_class = ManagerParticipantAddedOwnerNotification
        self.create()
        self.assertRecipients([self.owner])
        self.assertSubject('A participant has been added to your activity "Save the world!" 🎉')
        self.assertBodyContains('Frans Beckenbauer has been added to your activity "Save the world!"')
        self.assertActionLink(self.activity.get_absolute_url())
        self.assertActionTitle('Open your activity')

    def test_participant_added_notification(self):
        self.message_class = ParticipantAddedNotification
        self.obj = DateParticipantFactory.create(
            activity=self.activity,
            user=self.supporter,
        )
        self.create()
        self.assertRecipients([self.supporter])
        self.assertSubject('You have been added to the activity "Save the world!" 🎉')
        self.assertActionLink(self.activity.get_absolute_url())
        self.assertActionTitle('View activity')

    def test_participant_removed_owner_notification(self):
        self.message_class = ParticipantRemovedOwnerNotification
        self.create()
        self.assertRecipients([self.owner])
        self.assertSubject('A participant has been removed from your activity "Save the world!"')
        self.assertBodyContains('Frans Beckenbauer has been removed from your activity "Save the world!"')
        self.assertActionLink(self.activity.get_absolute_url())
        self.assertActionTitle('Open your activity')

    def test_participant_joined_notification(self):
        self.message_class = ParticipantJoinedNotification
        self.create()
        self.assertRecipients([self.supporter])
        self.assertSubject('You have joined the activity "Save the world!"')
        self.assertActionLink(self.activity.get_absolute_url())
        self.assertActionTitle('View activity')
        self.assertBodyContains(
            'Go to the activity page to see the times in your own timezone and add them to your calendar.'
        )


class PeriodParticipantNotificationTestCase(NotificationTestCase):

    def setUp(self):
        self.supporter = BlueBottleUserFactory.create(
            first_name='Frans',
            last_name='Beckenbauer'
        )
        self.owner = BlueBottleUserFactory.create()
        self.activity = PeriodActivityFactory.create(
            title="Save the world!",
            owner=self.owner,
            duration='1:30:00',
            duration_period='overall',
            review=False
        )
        self.obj = PeriodParticipantFactory.create(
            activity=self.activity,
            user=self.supporter
        )

    def test_participant_joined_notification(self):
        self.message_class = ParticipantJoinedNotification
        self.create()
        self.assertRecipients([self.supporter])
        self.assertSubject('You have joined the activity "Save the world!"')
        self.assertActionLink(self.activity.get_absolute_url())
        self.assertActionTitle('View activity')
        self.assertBodyNotContains(
            'Go to the activity page to see the times in your own timezone and add them to your calendar.'
        )

    def test_new_participant_notification(self):
        self.message_class = ParticipantAppliedNotification
        self.create()
        self.assertRecipients([self.supporter])
        self.assertSubject('You have applied to the activity "Save the world!"')
        self.assertActionLink(self.activity.get_absolute_url())
        self.assertActionTitle('View activity')

    def test_someone_applied_to_manager(self):
        self.activity.review_title = 'What is your favorite color?'
        self.obj.motivation = 'Vermilion'
        self.message_class = ParticipantCreatedNotification
        self.create()
        self.assertRecipients([self.activity.owner])
        self.assertSubject('You have a new participant for your activity "Save the world!" 🎉')
        self.assertBodyContains('Review the application and decide if this person is the right fit.')
        self.assertBodyContains('What is your favorite color?')
        self.assertBodyContains('Vermilion')


class DateSlotNotificationTestCase(NotificationTestCase):
    def setUp(self):
        self.activity = DateActivityFactory.create(
            title="Save the world!"
        )

        self.obj = DateActivitySlotFactory.create(
            activity=self.activity
        )

    def test_slot_cancelled(self):
        self.message_class = SlotCancelledNotification
        self.create()
        self.assertRecipients([self.activity.owner])
        self.assertSubject('A slot for your activity "Save the world!" has been cancelled')
        self.assertActionLink(self.activity.get_absolute_url())
        self.assertActionTitle('Open your activity')

    def test_slot_cancelled_with_participant(self):
        participant = DateParticipantFactory.create(activity=self.activity, status='accepted')
        SlotParticipantFactory.create(
            status='registered', slot=self.obj, participant=participant
        )
        SlotParticipantFactory.create(
            status='rejected',
            slot=self.obj,
            participant=DateParticipantFactory.create(activity=self.activity, status='accepted')
        )

        SlotParticipantFactory.create(
            status='registered',
            slot=self.obj,
            participant=DateParticipantFactory.create(activity=self.activity, status='rejected')
        )

        self.message_class = SlotCancelledNotification
        self.create()
        self.assertRecipients([self.activity.owner, participant.user])
        self.assertSubject('A slot for your activity "Save the world!" has been cancelled')
        self.assertActionLink(self.activity.get_absolute_url())
        self.assertActionTitle('Open your activity')


class DeadlineRegistrationNotificationTestCase(NotificationTestCase):

    def setUp(self):
        self.supporter = BlueBottleUserFactory.create(
            first_name='Frans',
            last_name='Beckenbauer'
        )

        self.activity = DeadlineActivityFactory.create(
            title="Save the world!",
            review=False
        )

        self.obj = DeadlineRegistrationFactory.create(
            activity=self.activity,
            user=self.supporter
        )

    def test_manager_registration_created(self):
        self.message_class = ManagerRegistrationCreatedNotification
        self.create()
        self.assertRecipients([self.activity.owner])
        self.assertSubject('You have a new participant for your activity "Save the world!" 🎉')
        self.assertActionLink(self.activity.get_absolute_url())
        self.assertActionTitle('Open your activity')

    def test_manager_registration_created_review(self):
        self.activity.review = True
        self.activity.save()
        self.message_class = ManagerRegistrationCreatedReviewNotification
        self.create()
        self.assertRecipients([self.activity.owner])
        self.assertSubject('You have a new application for your activity "Save the world!" 🎉')
        self.assertActionLink(self.activity.get_absolute_url())
        self.assertActionTitle('Open your activity')
