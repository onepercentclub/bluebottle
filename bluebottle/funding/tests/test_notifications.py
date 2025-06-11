from bluebottle.funding.messages.funding.activity_manager import FundingSubmittedMessage, FundingApprovedMessage, \
    FundingNeedsWorkMessage, FundingRejectedMessage
from bluebottle.funding.messages.funding.reviewer import FundingSubmittedReviewerMessage
from bluebottle.funding.messages.grant_application.activity_manager import GrantApplicationApprovedMessage, \
    GrantApplicationRejectedMessage, GrantApplicationSubmittedMessage, GrantApplicationCancelledMessage
from bluebottle.funding.messages.grant_application.reviewer import GrantApplicationSubmittedReviewerMessage
from bluebottle.funding.tests.factories import FundingFactory, GrantApplicationFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import NotificationTestCase


class FundingNotificationTestCase(NotificationTestCase):

    def setUp(self):
        self.obj = FundingFactory.create(
            title="Save the world!"
        )
        self.reviewer = BlueBottleUserFactory.create(
            is_staff=True,
            submitted_initiative_notifications=True
        )

    def test_activity_submitted_reviewer_notification(self):
        self.message_class = FundingSubmittedReviewerMessage
        self.create()
        self.assertRecipients([self.reviewer])
        self.assertSubject('A new crowdfunding campaign is ready to be reviewed on Test')
        self.assertBodyContains('Please take a moment to review this campaign')
        self.assertActionLink(self.obj.get_admin_url())
        self.assertActionTitle('View campaign')

    def test_activity_submitted_notification(self):
        self.message_class = FundingSubmittedMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('You submitted a crowdfunding campaign on Test')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View campaign')

    def test_activity_approved_notification(self):
        self.message_class = FundingApprovedMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your crowdfunding campaign on Test has been approved!')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View campaign')

    def test_activity_needs_work_notification(self):
        self.message_class = FundingNeedsWorkMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('The crowdfunding campaign you submitted on Test needs work')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View campaign')

    def test_activity_rejected_notification(self):
        self.message_class = FundingRejectedMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your crowdfunding campaign on Test has been rejected')
        self.assertBodyContains('Unfortunately your crowdfunding campaign "Save the world!" has been rejected.')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View campaign')


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
