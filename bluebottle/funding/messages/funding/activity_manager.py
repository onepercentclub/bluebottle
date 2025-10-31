# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.funding.models import Funding
from bluebottle.notifications.messages import TransitionMessage


class FundingActivityManagerMessage(TransitionMessage):
    context = {
        'title': 'title',
    }
    action_title = pgettext('email', 'View campaign')

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]

    class Meta:
        abstract = True
        model = Funding


class DonationSuccessActivityManagerMessage(FundingActivityManagerMessage):
    """
    Notify the activity manager that a donation was successful
    """
    subject = pgettext('email', "You have a new donation!💰")
    template = 'messages/funding/activity_manager/donation_success_owner'

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.activity.owner]


class FundingPartiallyFundedMessage(FundingActivityManagerMessage):
    """
    Notify the activity manager that their funding ended,m but didn't reach the target.
    """
    subject = pgettext('email', "Your crowdfunding campaign deadline passed")
    template = 'messages/funding/activity_manager/funding_partially_funded'


class FundingRealisedOwnerMessage(FundingActivityManagerMessage):
    """
    Notify the activity manager that their funding campaign was successful.
    """
    subject = pgettext('email', 'Your campaign "{title}" has been successfully completed! 🎉')
    template = 'messages/funding/activity_manager/funding_realised_owner'


class FundingRejectedMessage(FundingActivityManagerMessage):
    """
    Notify the activity manager that their funding campaign was rejected.
    """
    subject = pgettext('email', "Your crowdfunding campaign on {site_name} has been rejected")
    template = 'messages/funding/activity_manager/campaign_rejected'


class FundingSubmittedMessage(FundingActivityManagerMessage):
    """
    Notify the activity manager that their funding campaign was submitted.
    """
    subject = pgettext('email', "You submitted a crowdfunding campaign on {site_name}")
    template = 'messages/funding/activity_manager/campaign_submitted'


class FundingNeedsWorkMessage(FundingActivityManagerMessage):
    """
    Notify the activity manager that their funding campaign needs work.
    """
    subject = pgettext('email', u"The crowdfunding campaign you submitted on {site_name} needs work")
    template = 'messages/funding/activity_manager/campaign_needs_work'


class FundingExpiredMessage(FundingActivityManagerMessage):
    """
    Notify the activity manager that their funding campaign expired. The deadline passed with no donations.
    """
    subject = pgettext('email', u"Your crowdfunding campaign has expired")
    template = 'messages/funding/activity_manager/funding_expired'


class FundingRefundedMessage(FundingActivityManagerMessage):
    """
    Notify the activity manager that their funding campaign was refunded. All donations will be refunded to the donors.
    """
    subject = pgettext('email', u'The donations received for your campaign "{title}" will be refunded')
    template = 'messages/funding/activity_manager/funding_refunded'


class FundingApprovedMessage(FundingActivityManagerMessage):
    """
    Notify the activity manager that their funding campaign was approved.
    """
    subject = pgettext('email', 'Your crowdfunding campaign on {site_name} has been approved!')
    template = 'messages/funding/activity_manager/campaign_approved'


class FundingExtendedMessage(FundingActivityManagerMessage):
    """
    Notify the activity manager that the deadline for their funding campaign has been extended.
    """
    subject = pgettext('email', u'Your crowdfunding campaign "{title}" is open for new donations 💸')
    template = 'messages/funding/activity_manager/funding_extended'


class FundingCancelledMessage(FundingActivityManagerMessage):
    """
    Notify the activity manager that their funding campaign was cancelled.
    """
    subject = pgettext('email', u'Your crowdfunding campaign "{title}" has been cancelled')
    template = 'messages/funding/activity_manager/funding_cancelled'


class BaseFundingPayoutAccountMessage(FundingActivityManagerMessage):

    @property
    def activity(self):
        return self.obj.funding.last()

    @property
    def action_link(self):
        return self.activity.get_absolute_url()

    def get_recipients(self):
        """the activity organizer"""
        if self.activity:
            return [self.activity.owner]
        return []

    class Meta:
        abstract = True


class FundingPayoutAccountRejected(BaseFundingPayoutAccountMessage):
    """
    Notify the activity manager that the payout account has been rejected
    """
    subject = pgettext('email', u'Action required for your crowdfunding campaign')
    template = 'messages/funding/activity_manager/payout_account_rejected'


class FundingPayoutAccountMarkedIncomplete(BaseFundingPayoutAccountMessage):
    """
    Notify the activity manager that the payout account has been marked incomplete
    """
    subject = pgettext('email', "Action required for your crowdfunding campaign")
    template = "messages/funding/activity_manager/payout_account_marked_incomplete"


class FundingPayoutAccountVerified(BaseFundingPayoutAccountMessage):
    """
    Notify the activity manager that the payout account has been verified
    """
    subject = pgettext('email', u'Your identity has been verified on {site_name}')
    template = 'messages/funding/activity_manager/payout_account_verified'


class FundingPublicPayoutAccountRejected(BaseFundingPayoutAccountMessage):
    """
    Notify the activity manager that the public payout account has been rejected
    """
    subject = pgettext('email', u'Action required for your identity verification')
    template = 'messages/funding/activity_manager/public_payout_account_rejected'


class FundingPublicPayoutAccountMarkedIncomplete(BaseFundingPayoutAccountMessage):
    """
    Notify the activity manager that the public payout account has been marked incomplete
    """
    subject = pgettext('email', "Action required for identity verification")
    template = "messages/funding/activity_manager/public_payout_account_marked_incomplete"


class FundingPublicPayoutAccountVerified(BaseFundingPayoutAccountMessage):
    """
    Notify the activity manager that the public payout account has been verified
    """
    subject = pgettext('email', u'Your identity has been verified on {site_name}')
    template = 'messages/funding/activity_manager/public_payout_account_verified'
