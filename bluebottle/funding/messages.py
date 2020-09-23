# -*- coding: utf-8 -*-
from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class DonationSuccessActivityManagerMessage(TransitionMessage):
    subject = _(u"You have a new donation!💰")
    template = 'messages/donation_success_owner'

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.activity.owner]


class DonationSuccessDonorMessage(TransitionMessage):
    subject = _("Thanks for your donation!")
    template = 'messages/donation_success_donor'

    def get_recipients(self):
        """the donor (unless it is a guest donation)"""
        if self.obj.user:
            return [self.obj.user]
        # Guest donation. Return empty list so no mails are send.
        return []


class DonationRefundedDonorMessage(TransitionMessage):
    subject = _('Your donation for the campaign "{title}" will be refunded')
    template = 'messages/donation_refunded_donor'

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
    subject = _(u"Your crowdfunding campaign deadline passed")
    template = 'messages/funding_partially_funded'

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class FundingRealisedOwnerMessage(TransitionMessage):
    subject = _(u'Your campaign "{title}" has been successfully completed! 🎉')
    template = 'messages/funding_realised_owner'

    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class FundingRejectedMessage(TransitionMessage):
    subject = _(u"Your crowdfunding campaign has been rejected.")
    template = 'messages/funding_rejected'

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class FundingExpiredMessage(TransitionMessage):
    subject = _(u"Your crowdfunding campaign has expired")
    template = 'messages/funding_expired'

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class FundingRefundedMessage(TransitionMessage):
    subject = _(u'The donations received for your campaign "{title}" will be refunded')
    template = 'messages/funding_refunded'

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

    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class FundingExtendedMessage(TransitionMessage):
    subject = _(u'Your campaign "{title}" is open for new donations 💸')
    template = 'messages/funding_extended'

    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class FundingCancelledMessage(TransitionMessage):
    subject = _(u'Your campaign "{title}" has been cancelled')
    template = 'messages/funding_cancelled'

    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class PayoutAccountRejected(TransitionMessage):
    subject = _(u'Your identity verification needs some work')
    template = 'messages/payout_account_rejected'

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class PayoutAccountVerified(TransitionMessage):
    subject = _(u'Your identity has been verified')
    template = 'messages/payout_account_verified'

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]
