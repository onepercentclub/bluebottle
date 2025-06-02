# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext

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


class DonationSuccessActivityManagerMessage(FundingActivityManagerMessage):
    subject = _("You have a new donation!💰")
    template = 'messages/activity_manager/donation_success_owner'

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.activity.owner]


class FundingPartiallyFundedMessage(FundingActivityManagerMessage):
    subject = _("Your crowdfunding campaign deadline passed")
    template = 'messages/funding/activity_manager/funding_partially_funded'


class FundingRealisedOwnerMessage(FundingActivityManagerMessage):
    subject = _('Your campaign "{title}" has been successfully completed! 🎉')
    template = 'messages/funding/activity_manager/funding_realised_owner'


class FundingRejectedMessage(FundingActivityManagerMessage):
    subject = _("Your crowdfunding campaign on {site_name} has been rejected")
    template = 'messages/funding/activity_manager/campaign_rejected'


class FundingSubmittedMessage(FundingActivityManagerMessage):
    subject = _("You submitted a crowdfunding campaign on {site_name}")
    template = 'messages/funding/activity_manager/campaign_submitted'


class FundingNeedsWorkMessage(FundingActivityManagerMessage):
    subject = _(u"The crowdfunding campaign you submitted on {site_name} needs work")
    template = 'messages/funding/activity_manager/campaign_needs_work'


class FundingExpiredMessage(FundingActivityManagerMessage):
    subject = _(u"Your crowdfunding campaign has expired")
    template = 'messages/funding/activity_manager/funding_expired'


class FundingRefundedMessage(FundingActivityManagerMessage):
    subject = _(u'The donations received for your campaign "{title}" will be refunded')
    template = 'messages/funding/activity_manager/funding_refunded'


class FundingApprovedMessage(FundingActivityManagerMessage):
    subject = _('Your crowdfunding campaign on {site_name} has been approved!')
    template = 'messages/funding/activity_manager/campaign_approved'


class FundingExtendedMessage(FundingActivityManagerMessage):
    subject = _(u'Your crowdfunding campaign "{title}" is open for new donations 💸')
    template = 'messages/funding/activity_manager/funding_extended'


class FundingCancelledMessage(FundingActivityManagerMessage):
    subject = _(u'Your crowdfunding campaign "{title}" has been cancelled')
    template = 'messages/funding/activity_manager/funding_cancelled'


class PayoutAccountRejected(FundingActivityManagerMessage):
    subject = _(u'Action required for your crowdfunding campaign')
    template = 'messages/funding/activity_manager/payout_account_rejected'


class PayoutAccountMarkedIncomplete(FundingActivityManagerMessage):
    subject = _("Action required for your crowdfunding campaign")
    template = "messages/funding/activity_manager/payout_account_marked_incomplete"


class PayoutAccountVerified(FundingActivityManagerMessage):
    subject = _(u'Your identity has been verified')
    template = 'messages/funding/activity_manager/payout_account_verified'


class PublicPayoutAccountRejected(PayoutAccountRejected):
    subject = _(u'Action required for your identity verification')
    template = 'messages/activity_manager/public_payout_account_rejected'


class PublicPayoutAccountMarkedIncomplete(PayoutAccountMarkedIncomplete):
    subject = _("Action required for identity verification")
    template = "messages/activity_manager/public_payout_account_marked_incomplete"


class PublicPayoutAccountVerified(TransitionMessage):
    subject = _(u'Your identity has been verified')
    template = 'messages/activity_manager/public_payout_account_verified'
