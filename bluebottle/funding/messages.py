# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from bluebottle.funding.models import Donor, Funding, PayoutAccount
from bluebottle.notifications.messages import TransitionMessage


class DonationSuccessActivityManagerMessage(TransitionMessage):
    """
    Someone donated to your funding campaign
    """
    subject = _(u"You have a new donation!💰")
    template = 'messages/donation_success_owner'
    model = Donor

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.activity.owner]


class DonationSuccessDonorMessage(TransitionMessage):
    """
    You just donated to a funding campaign
    """
    subject = _("Thanks for your donation!")
    template = 'messages/donation_success_donor'
    model = Donor

    def get_recipients(self):
        """the donor (unless it is a guest donation)"""
        if self.obj.user:
            return [self.obj.user]
        # Guest donation. Return empty list so no mails are send.
        return []


class DonationRefundedDonorMessage(TransitionMessage):
    """
    Your donation has been refunded
    """
    subject = _('Your donation for the campaign "{title}" will be refunded')
    template = 'messages/donation_refunded_donor'
    model = Donor

    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """the donor (unless it is a guest donation)"""
        if self.obj.user:
            return [self.obj.user]
        # Guest donation. Return empty list so no mails are send.
        return []


class DonationActivityRefundedDonorMessage(TransitionMessage):
    subject = _('Your donation for the campaign "{title}" will be refunded')
    template = 'messages/donation_activity_refunded_donor'
    model = Donor

    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """the donor (unless it is a guest donation)"""
        if self.obj.user:
            return [self.obj.user]
        # Guest donation. Return empty list so no mails are send.
        return []


class FundingPartiallyFundedMessage(TransitionMessage):
    """
    Your funding campaign ended and was partially funded
    """
    subject = _(u"Your crowdfunding campaign deadline passed")
    template = 'messages/funding_partially_funded'
    model = Funding

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class FundingRealisedOwnerMessage(TransitionMessage):
    """
    Your funding campaign ended successfully
    """
    subject = _(u'Your campaign "{title}" has been successfully completed! 🎉')
    template = 'messages/funding_realised_owner'
    model = Funding

    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class FundingRejectedMessage(TransitionMessage):
    """
    Your funding campaign was rejected
    """
    subject = _(u"Your crowdfunding campaign has been rejected.")
    template = 'messages/funding_rejected'
    model = Funding

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class FundingExpiredMessage(TransitionMessage):
    """
    Your funding campaign was closed
    """
    subject = _(u"Your crowdfunding campaign has expired")
    template = 'messages/funding_expired'
    model = Funding

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class FundingRefundedMessage(TransitionMessage):
    subject = _(u'The donations received for your campaign "{title}" will be refunded')
    template = 'messages/funding_refunded'
    model = Funding

    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class FundingApprovedMessage(TransitionMessage):
    subject = _(
        u'Your campaign "{title}" is approved and is now open for donations 💸'
    )
    template = 'messages/funding_approved'
    model = Funding

    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class FundingExtendedMessage(TransitionMessage):
    subject = _(u'Your campaign "{title}" is open for new donations 💸')
    template = 'messages/funding_extended'
    model = Funding

    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class FundingCancelledMessage(TransitionMessage):
    subject = _(u'Your campaign "{title}" has been cancelled')
    template = 'messages/funding_cancelled'
    model = Funding

    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class PayoutAccountRejected(TransitionMessage):
    """
    Your identity verification was rejected
    """
    subject = _(u'Your identity verification needs some work')
    template = 'messages/payout_account_rejected'
    model = PayoutAccount

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class PayoutAccountVerified(TransitionMessage):
    """
    Your identity verification has been approved
    """
    subject = _(u'Your identity has been verified')
    template = 'messages/payout_account_verified'
    model = PayoutAccount

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]
