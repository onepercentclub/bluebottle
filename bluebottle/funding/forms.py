from django import forms
from django.utils.translation import gettext_lazy as _

from bluebottle.funding.messages.funding.activity_manager import (
    FundingApprovedMessage,
    FundingNeedsWorkMessage,
    FundingRejectedMessage, FundingRefundedMessage,
)
from bluebottle.utils.forms import TransitionConfirmationForm


class RefundConfirmationForm(forms.Form):
    title = _('Refund payment')
    message = FundingRefundedMessage


class FundingNeedsWorkForm(TransitionConfirmationForm):
    title = _('Funding needs work')
    message_class = FundingNeedsWorkMessage


class FundingRejectedForm(TransitionConfirmationForm):
    title = _('Activity rejected')
    message_class = FundingRejectedMessage


class FundingAcceptedForm(TransitionConfirmationForm):
    title = _('Crowdfunding campaign accepted')
    message_class = FundingApprovedMessage
