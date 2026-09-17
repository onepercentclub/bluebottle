from django.contrib.auth.models import Group

from bluebottle.activities.messages.activity_manager import TermsOfServiceNotification
from bluebottle.funding.messages.funding.activity_manager import FundingSubmittedMessage, FundingApprovedMessage, \
    FundingNeedsWorkMessage, FundingRejectedMessage
from bluebottle.funding.messages.funding.platform_manager import LivePayoutAccountMarkedIncomplete
from bluebottle.funding.messages.funding.reviewer import FundingSubmittedReviewerMessage
from bluebottle.funding.models import Funding
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.funding_stripe.tests.base import FundingStripeMixin, save_stripe_payout_account
from bluebottle.funding_stripe.tests.factories import ExternalAccountFactory, StripePayoutAccountFactory
from bluebottle.grant_management.models import GrantApplication
from bluebottle.grant_management.tests.factories import GrantApplicationFactory
from bluebottle.offices.tests.factories import LocationFactory, OfficeSubRegionFactory
from bluebottle.segments.tests.factories import SegmentFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import NotificationTestCase


def reviewer_with_permission(**extra):
    reviewer = BlueBottleUserFactory.create(
        submitted_initiative_notifications=True,
        **extra
    )
    reviewer.groups.add(Group.objects.get(name='Staff'))
    return reviewer


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

    def test_activity_terms_notification(self):
        self.message_class = TermsOfServiceNotification
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Terms of service')
        self.assertBodyContains('Thanks for creating a crowdfunding campaign for')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View campaign')

    def test_activity_needs_work_notification(self):
        self.message_class = FundingNeedsWorkMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your crowdfunding campaign on Test needs work')
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


class LivePayoutAccountMarkedIncompleteNotificationTestCase(FundingStripeMixin, NotificationTestCase):

    def setUp(self):
        super().setUp()
        self.payout_account = StripePayoutAccountFactory.create(
            status='verified',
            account_id='test-live-payout-account',
        )
        save_stripe_payout_account(self.payout_account)
        self.bank_account = ExternalAccountFactory.create(connect_account=self.payout_account)
        self.obj = self.payout_account
        self.global_reviewer = reviewer_with_permission()
        self.message_class = LivePayoutAccountMarkedIncomplete

    def create_message(self):
        self.create()

    def _grant_application(self, status, bank_account=None):
        application = GrantApplicationFactory.create(status='draft')
        updates = {'status': status}
        if bank_account is not None:
            updates['bank_account_id'] = bank_account.pk
        GrantApplication.objects.filter(pk=application.pk).update(**updates)
        application.refresh_from_db()
        return application

    def _granted_grant_application(self, bank_account=None):
        return self._grant_application('granted', bank_account=bank_account or self.bank_account)

    def _other_bank_account(self):
        other_payout_account = StripePayoutAccountFactory.create(
            status='verified',
            account_id='other-live-payout-account',
        )
        save_stripe_payout_account(other_payout_account)
        return ExternalAccountFactory.create(connect_account=other_payout_account)

    def test_open_funding_notifies_activity_reviewers(self):
        FundingFactory.create(status='open', bank_account=self.bank_account)
        self.create_message()
        self.assertRecipients([self.global_reviewer])

    def test_on_hold_funding_notifies_activity_reviewers(self):
        FundingFactory.create(status='on_hold', bank_account=self.bank_account)
        self.create_message()
        self.assertRecipients([self.global_reviewer])

    def test_draft_funding_does_not_notify(self):
        FundingFactory.create(status='draft', bank_account=self.bank_account)
        self.create_message()
        self.assertRecipients([])

    def test_inactive_funding_status_does_not_notify(self):
        for status in ['succeeded', 'cancelled', 'rejected']:
            with self.subTest(status=status):
                Funding.objects.all().delete()
                FundingFactory.create(status=status, bank_account=self.bank_account)
                self.create_message()
                self.assertRecipients([])

    def test_unrelated_funding_does_not_notify(self):
        other_bank_account = self._other_bank_account()
        FundingFactory.create(status='open', bank_account=other_bank_account)
        self.create_message()
        self.assertRecipients([])

    def test_granted_grant_application_notifies_activity_reviewers(self):
        self._granted_grant_application()
        self.create_message()
        self.assertRecipients([self.global_reviewer])

    def test_non_granted_grant_application_does_not_notify(self):
        for status in ['draft', 'open', 'submitted', 'succeeded']:
            with self.subTest(status=status):
                GrantApplication.objects.all().delete()
                self._grant_application(status, bank_account=self.bank_account)
                self.create_message()
                self.assertRecipients([])

    def test_open_funding_and_granted_application_deduplicate_recipients(self):
        FundingFactory.create(status='open', bank_account=self.bank_account)
        self._granted_grant_application()
        self.create_message()
        self.assertRecipients([self.global_reviewer])

    def test_segment_manager_only_notified_for_matching_segment(self):
        segment = SegmentFactory.create()
        other_segment = SegmentFactory.create()
        funding = FundingFactory.create(status='open', bank_account=self.bank_account)
        funding.segments.add(segment)

        matching_reviewer = reviewer_with_permission()
        matching_reviewer.segment_manager.add(segment)
        non_matching_reviewer = reviewer_with_permission()
        non_matching_reviewer.segment_manager.add(other_segment)

        self.create_message()
        self.assertRecipients([self.global_reviewer, matching_reviewer])

    def test_office_manager_only_notified_for_matching_office(self):
        office = LocationFactory.create()
        other_office = LocationFactory.create()
        FundingFactory.create(
            status='open',
            bank_account=self.bank_account,
            office_location=office,
        )

        matching_reviewer = reviewer_with_permission()
        matching_reviewer.office_manager.add(office)
        non_matching_reviewer = reviewer_with_permission()
        non_matching_reviewer.office_manager.add(other_office)

        self.create_message()
        self.assertRecipients([self.global_reviewer, matching_reviewer])

    def test_subregion_manager_only_notified_for_matching_subregion(self):
        subregion = OfficeSubRegionFactory.create()
        other_subregion = OfficeSubRegionFactory.create()
        FundingFactory.create(
            status='open',
            bank_account=self.bank_account,
            office_location=LocationFactory.create(subregion=subregion),
        )

        matching_reviewer = reviewer_with_permission()
        matching_reviewer.subregion_manager.add(subregion)
        non_matching_reviewer = reviewer_with_permission()
        non_matching_reviewer.subregion_manager.add(other_subregion)

        self.create_message()
        self.assertRecipients([self.global_reviewer, matching_reviewer])

    def test_excludes_reviewers_without_notifications_enabled(self):
        FundingFactory.create(status='open', bank_account=self.bank_account)
        self.global_reviewer.submitted_initiative_notifications = False
        self.global_reviewer.save()
        self.create_message()
        self.assertRecipients([])

    def test_excludes_members_without_review_permission(self):
        FundingFactory.create(status='open', bank_account=self.bank_account)
        BlueBottleUserFactory.create(submitted_initiative_notifications=True)
        self.create_message()
        self.assertRecipients([self.global_reviewer])
