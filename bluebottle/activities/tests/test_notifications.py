from datetime import timedelta

from django.utils.timezone import now

from bluebottle.activities.messages.activity_manager import (
    ActivityRejectedNotification, ActivityCancelledNotification,
    ActivitySucceededNotification, ActivityRestoredNotification,
    ActivityExpiredNotification,
    ActivitySubmittedNotification, ActivityPublishedNotification,
    ActivityApprovedNotification, ActivityNeedsWorkNotification
)
from bluebottle.activities.messages.matching import (
    DoGoodHoursReminderQ1Notification,
    DoGoodHoursReminderQ2Notification,
    DoGoodHoursReminderQ3Notification,
    DoGoodHoursReminderQ4Notification,
)
from bluebottle.activities.messages.reviewer import ActivitySubmittedReviewerNotification, \
    ActivityPublishedReviewerNotification
from bluebottle.members.models import MemberPlatformSettings, Member
from bluebottle.notifications.models import NotificationPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import NotificationTestCase
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, DateActivitySlotFactory,
    DateParticipantFactory, DateRegistrationFactory
)


class ActivityNotificationTestCase(NotificationTestCase):

    def setUp(self):
        self.obj = DateActivityFactory.create(
            title="Save the world!"
        )
        self.reviewer = BlueBottleUserFactory.create(
            is_staff=True,
            submitted_initiative_notifications=True
        )

    def test_activity_submitted_reviewer_notification(self):
        self.message_class = ActivitySubmittedReviewerNotification
        self.create()
        self.assertRecipients([self.reviewer])
        self.assertSubject('A new activity is ready to be reviewed on Test')
        self.assertBodyContains('Please take a moment to review this activity')
        self.assertActionLink(self.obj.get_admin_url())
        self.assertActionTitle('View this activity')

    def test_activity_published_reviewer_notification(self):
        self.message_class = ActivityPublishedReviewerNotification
        self.create()
        self.assertRecipients([self.reviewer])
        self.assertSubject('A new activity has been published on Test')
        self.assertBodyContains('has been successfully published')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View this activity')

    def test_activity_submitted_notification(self):
        self.message_class = ActivitySubmittedNotification
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('You submitted an activity on Test')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('Open your activity')

    def test_activity_published_notification(self):
        self.message_class = ActivityPublishedNotification
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your activity on Test has been published!')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('Open your activity')

    def test_activity_approved_notification(self):
        self.message_class = ActivityApprovedNotification
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your activity on Test has been approved!')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('Open your activity')

    def test_activity_needs_work_notification(self):
        self.message_class = ActivityNeedsWorkNotification
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('The activity you submitted on Test needs work')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('Open your activity')

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


class DoGoodHoursReminderNotificationTestCase(NotificationTestCase):

    def setUp(self):
        self.obj = NotificationPlatformSettings.load()
        self.obj = MemberPlatformSettings.load()
        self.obj.do_good_hours = 8
        self.obj.save()
        activity = DateActivityFactory.create(
            slots=[],
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
        reg1 = DateRegistrationFactory.create(
            user=self.active_user,
            activity=activity
        )
        DateParticipantFactory.create(
            registration=reg1,
            slot=slot1
        )
        DateParticipantFactory.create(
            registration=reg1,
            slot=slot2
        )
        self.moderate_user = BlueBottleUserFactory.create(first_name='Moderate')
        reg2 = DateRegistrationFactory.create(
            user=self.moderate_user,
            activity=activity
        )
        DateParticipantFactory.create(
            registration=reg2,
            slot=slot1
        )
        DateParticipantFactory.create(
            registration=reg2,
            slot=old_slot
        )
        self.passive_user = BlueBottleUserFactory.create(first_name='Passive')
        reg3 = DateRegistrationFactory.create(
            user=self.passive_user,
            activity=activity
        )

        DateParticipantFactory.create(
            registration=reg3,
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
        self.assertSubject("It’s a new year, let's make some impact!")
        self.assertBodyContains('Can you spend 8 hours making an impact this year?')
        self.assertActionTitle('Find activities')
        self.assertActionLink('http://test.localhost:8000/initiatives/activities/list')
        self.assertBodyContains('http://test.localhost:8000/member/profile')

    def test_reminder_q2(self):
        self.message_class = DoGoodHoursReminderQ2Notification
        self.create()
        self.assertRecipients([self.moderate_user, self.passive_user])
        self.assertSubject("Haven’t joined an activity yet? Let’s get started!")
        self.assertBodyContains('The first step is always the hardest')
        self.assertActionTitle('Find activities')

    def test_reminder_q3(self):
        self.message_class = DoGoodHoursReminderQ3Notification
        self.create()
        self.assertRecipients([self.moderate_user, self.passive_user])
        self.assertSubject("Half way through the year and still plenty of activities to join")
        self.assertBodyContains(
            'There’s still so much time to reach the target of 8 hours making an impact this year.'
        )
        self.assertActionTitle('Find activities')

    def test_reminder_q4(self):
        self.message_class = DoGoodHoursReminderQ4Notification
        self.create()
        self.assertRecipients([self.moderate_user, self.passive_user])
        self.assertSubject("Make use of your 8 hours of impact!")
        self.assertBodyContains(
            'Get involved with some good causes before the year ends, '
            'there are plenty of activities that need your help!'
        )
        self.assertActionTitle('Find activities')
