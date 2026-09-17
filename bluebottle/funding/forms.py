from django import forms
from django.utils.translation import gettext_lazy as _

from bluebottle.funding.messages.funding.activity_manager import (
    FundingApprovedMessage,
    FundingNeedsWorkMessage,
    FundingRejectedMessage, FundingRefundedMessage, FundingCancelledMessage,
)
from bluebottle.utils.forms import TransitionConfirmationForm


class RefundConfirmationForm(forms.Form):
    title = _('Refund payment')


class FundingNeedsWorkForm(TransitionConfirmationForm):
    title = _('Crowdfunding campaign needs work')
    message_class = FundingNeedsWorkMessage


class FundingRejectedForm(TransitionConfirmationForm):
    title = _('Crowdfunding campaign rejected')
    message_class = FundingRejectedMessage


class FundingAcceptedForm(TransitionConfirmationForm):
    title = _('Crowdfunding campaign accepted')
    message_class = FundingApprovedMessage


class RefundCampaignForm(TransitionConfirmationForm):
    title = _('Refund crowdfunding campaign')
    message_class = FundingRefundedMessage


class CancelCampaignForm(TransitionConfirmationForm):
    title = _('Cancel crowdfunding campaign')
    message_class = FundingCancelledMessage
