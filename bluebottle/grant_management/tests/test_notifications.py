from bluebottle.grant_management.messages.activity_manager import GrantApplicationApprovedMessage, \
    GrantApplicationRejectedMessage, GrantApplicationSubmittedMessage, GrantApplicationCancelledMessage
from bluebottle.grant_management.messages.reviewer import GrantApplicationSubmittedReviewerMessage
from bluebottle.grant_management.tests.factories import GrantApplicationFactory

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import NotificationTestCase


class GrantApplicationNotificationTestCase(NotificationTestCase):

    def setUp(self):
        self.obj = GrantApplicationFactory.create(
            title="Save the world!"
        )
        self.reviewer = BlueBottleUserFactory.create(
            is_staff=True,
            submitted_initiative_notifications=True
        )

    def test_activity_approved_notification(self):
        self.message_class = GrantApplicationApprovedMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your grant application on Test has been approved!')
        self.assertBodyContains('Good news, your grant application')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View application')

    def test_activity_rejected_notification(self):
        self.message_class = GrantApplicationRejectedMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your grant application on Test has been rejected')
        self.assertBodyContains('Unfortunately your grant application')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View application')

    def test_activity_submitted_notification(self):
        self.message_class = GrantApplicationSubmittedMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('You have submitted a grant application on Test')
        self.assertBodyContains('has been submitted')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View application')

    def test_activity_submitted_reviewer_notification(self):
        self.message_class = GrantApplicationSubmittedReviewerMessage
        self.create()
        self.assertRecipients([self.reviewer])
        self.assertSubject('A new grant application is ready to be reviewed on Test')
        self.assertBodyContains('Please take a moment to review this application')
        self.assertActionLink(self.obj.get_admin_url())
        self.assertActionTitle('View application')

    def test_activity_cancelled_notification(self):
        self.message_class = GrantApplicationCancelledMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your grant application on Test has been cancelled')
        self.assertBodyContains('Unfortunately your grant application')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View application')
