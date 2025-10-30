# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _, pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage


class DonationSuccessDonorMessage(TransitionMessage):
    subject = pgettext('email', "Thanks for your donation!")
    template = 'messages/funding/contributor/donation_success_donor'

    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """the donor (unless it is a guest donation)"""
        if self.obj.user:
            return [self.obj.user]
        # Guest donation. Return empty list so no mails are send.
        return []


class DonationRefundedDonorMessage(TransitionMessage):
    subject = pgettext('email', 'Your donation for the campaign "{title}" will be refunded')
    template = 'messages/funding/contributor/donation_refunded_donor'

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
    subject = pgettext('email', 'Your donation for the campaign "{title}" will be refunded')
    template = 'messages/funding/contributor/donation_activity_refunded_donor'

    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """the donor (unless it is a guest donation)"""
        if self.obj.user:
            return [self.obj.user]
        # Guest donation. Return empty list so no mails are send.
        return []
