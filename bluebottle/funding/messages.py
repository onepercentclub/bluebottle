# -*- coding: utf-8 -*-
from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class DonationSuccessActivityManagerMessage(TransitionMessage):
    subject = _(u"You have a new donation!💰")
    template = 'messages/donation_success_activity_owner'

    def get_recipients(self):
        return [self.obj.activity.owner]


class DonationSuccessDonorMessage(TransitionMessage):
    subject = _("Thanks for your donation!")
    template = 'messages/donation_success_donor'

    def get_recipients(self):
        if self.obj.user:
            return [self.obj.user]
        # Guest donation. Return empty list so no mails are send.
        return []


class DonationRefundedDonorMessage(TransitionMessage):
    subject = _("Your donation has been refunded")
    template = 'messages/donation_refunded_donor'

    def get_recipients(self):
        if self.obj.user:
            return [self.obj.user]
        # Guest donation. Return empty list so no mails are send.
        return []


class FundingPartiallyFundedMessage(TransitionMessage):
    subject = _(u"Your funding deadline passed")
    template = 'messages/funding_partially_funded'

    def get_recipients(self):
        return [self.obj.activity.owner]


class FundingRealisedOwnerMessage(TransitionMessage):
    subject = _(u"You successfully completed your crowdfunding campaign! 🎉")
    template = 'messages/funding_realised_owner'

    def get_recipients(self):
        return [self.obj.activity.owner]


class FundingClosedMessage(TransitionMessage):
    subject = _(u"You have a new donation!💰")
    template = 'messages/donation_success_activity_owner'

    def get_recipients(self):
        return [self.obj.activity.owner]
