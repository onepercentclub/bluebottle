from bluebottle.funding.messages.activity_manager import (
    FundingSubmittedMessage, FundingApprovedMessage, FundingNeedsWorkMessage,
    FundingRejectedMessage
)
from bluebottle.funding.messages.reviewer import FundingSubmittedReviewerMessage
from bluebottle.funding.tests.factories import FundingFactory
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
        self.assertSubject('A new crowdfunding campaign is ready to be reviewed on [site name]')
        self.assertBodyContains('Please take a moment to review this campaign')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View campaign')

    def test_activity_submitted_notification(self):
        self.message_class = FundingSubmittedMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('You submitted a crowdfunding campaign on [site name]')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View campaign')

    def test_activity_approved_notification(self):
        self.message_class = FundingApprovedMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your crowdfunding campaign on [site name] has been approved!')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View campaign')

    def test_activity_needs_work_notification(self):
        self.message_class = FundingNeedsWorkMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('The crowdfunding campaign you submitted on [site name] needs work')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View campaign')

    def test_activity_rejected_notification(self):
        self.message_class = FundingRejectedMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your crowdfunding campaign on [site name] has been rejected')
        self.assertBodyContains('Unfortunately your crowdfunding campaign "Save the world!" has been rejected.')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View campaign')
