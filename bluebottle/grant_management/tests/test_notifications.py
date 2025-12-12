from djmoney.money import Money

from bluebottle.activities.messages.activity_manager import TermsOfServiceNotification
from bluebottle.grant_management.messages.activity_manager import GrantApplicationApprovedMessage, \
    GrantApplicationRejectedMessage, GrantApplicationSubmittedMessage, GrantApplicationCancelledMessage
from bluebottle.grant_management.messages.grant_provider import GrantPaymentRequestMessage
from bluebottle.grant_management.messages.reviewer import GrantApplicationSubmittedReviewerMessage, \
    PayoutReadyForApprovalMessage
from bluebottle.grant_management.tests.factories import GrantApplicationFactory, GrantPaymentFactory, \
    GrantPayoutFactory, GrantDonorFactory, GrantProviderFactory, GrantFundFactory
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

    def test_activity_terms_notification(self):
        self.message_class = TermsOfServiceNotification
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Terms of service')
        self.assertBodyContains('Thanks for creating a grant application for')
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


class GrantPaymentNotificationTestCase(NotificationTestCase):

    def setUp(self):
        finance_manager = BlueBottleUserFactory.create()
        provider = GrantProviderFactory.create(
            name="Test Provider",
            owner=finance_manager
        )
        fund = GrantFundFactory.create(
            name="Test Fund",
            grant_provider=provider
        )

        self.obj = GrantPaymentFactory.create()
        grant_application1 = GrantApplicationFactory.create(
            title="Save the world!",
            status='granted'
        )
        payout1 = GrantPayoutFactory.create(
            payment=self.obj,
            activity=grant_application1,
            status='approved',
        )
        GrantDonorFactory.create(
            payout=payout1,
            activity=grant_application1,
            fund=fund,
            amount=Money(2000, 'EUR')
        )

        grant_application2 = GrantApplicationFactory.create(
            title="Save the world!",
            status='granted'
        )
        payout2 = GrantPayoutFactory.create(
            payment=self.obj,
            activity=grant_application2,
            status='approved'
        )

        GrantDonorFactory.create(
            payout=payout2,
            activity=grant_application2,
            fund=fund,
            amount=Money(1500, 'EUR')
        )

    def test_payment_request_notification(self):
        self.message_class = GrantPaymentRequestMessage
        self.create()
        self.assertRecipients([self.obj.grant_provider.owner])
        self.assertSubject('A grant payment request is ready on Test')
        self.assertActionLink(self.obj.get_admin_url())
        self.assertActionTitle('Pay now')


class GrantPayoutNotificationTestCase(NotificationTestCase):

    def setUp(self):
        self.reviewer = BlueBottleUserFactory.create(
            is_staff=True,
            submitted_initiative_notifications=True
        )
        finance_manager = BlueBottleUserFactory.create()
        provider = GrantProviderFactory.create(
            name="Test Provider",
            owner=finance_manager
        )
        fund = GrantFundFactory.create(
            name="Test Fund",
            grant_provider=provider
        )

        self.grant_application = GrantApplicationFactory.create(
            title="Save the whales!",
            status='granted'
        )
        self.obj = GrantPayoutFactory.create(
            activity=self.grant_application,
            status='new',
        )
        GrantDonorFactory.create(
            payout=self.obj,
            activity=self.grant_application,
            fund=fund,
            amount=Money(5000, 'EUR')
        )

    def test_payout_ready_for_approval_notification(self):
        self.message_class = PayoutReadyForApprovalMessage
        self.create()
        self.assertRecipients([self.reviewer])
        self.assertSubject('You have grant payout to approve on Test')
        self.assertBodyContains('Save the whales!')
        self.assertBodyContains('Test Fund')
        self.assertActionLink(self.obj.get_admin_url())
        self.assertActionTitle('Complete payout')
