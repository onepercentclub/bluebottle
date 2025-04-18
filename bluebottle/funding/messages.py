# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from bluebottle.members.models import Member
from bluebottle.notifications.messages import TransitionMessage


class DonationSuccessActivityManagerMessage(TransitionMessage):
    subject = _(u"You have a new donation!💰")
    template = 'messages/donation_success_owner'

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.activity.owner]


class DonationSuccessDonorMessage(TransitionMessage):
    subject = _("Thanks for your donation!")
    template = 'messages/donation_success_donor'

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

    context = {
        'title': 'title'
    }

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
    subject = _(u'Action required for your crowdfunding campaign')
    template = 'messages/payout_account_rejected'

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class PayoutAccountMarkedIncomplete(TransitionMessage):
    subject = _("Action required for your crowdfunding campaign")
    template = "messages/payout_account_marked_incomplete"

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class LivePayoutAccountMarkedIncomplete(TransitionMessage):
    subject = _(u'Live campaign identity verification failed!')
    template = 'messages/live_payout_account_rejected'

    context = {
        'id': 'id'
    }

    def get_recipients(self):
        """platform support email addresses"""
        members = []
        for email in settings.SUPPORT_EMAIL_ADDRESSES:
            member, _c = Member.objects.get_or_create(email=email)
            members.append(member)
        for member in Member.objects.filter(submitted_initiative_notifications=True).all():
            members.append(member)
        return members


class PayoutAccountVerified(TransitionMessage):
    subject = _(u'Your identity has been verified')
    template = 'messages/payout_account_verified'

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class PublicPayoutAccountRejected(PayoutAccountRejected):
    subject = _(u'Action required for your identity verification')
    template = 'messages/public_payout_account_rejected'


class PublicPayoutAccountMarkedIncomplete(PayoutAccountMarkedIncomplete):
    subject = _("Action required for identity verification")
    template = "messages/public_payout_account_marked_incomplete"


class LivePublicPayoutAccountMarkedIncomplete(LivePayoutAccountMarkedIncomplete):
    subject = _(u'Incomplete payout account for running campaign')
    template = 'messages/live_public_payout_account_rejected'


class PublicPayoutAccountVerified(TransitionMessage):
    subject = _(u'Your identity has been verified')
    template = 'messages/public_payout_account_verified'


class NewRequirementsMessage(TransitionMessage):
    subject = _("We need more information before your account can be verified")
    template = "messages/payout_account_new_requirements"

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]
