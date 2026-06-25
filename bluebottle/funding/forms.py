from django import forms
from django.utils.translation import gettext_lazy as _

from bluebottle.utils.forms import CustomMessageFormField, TransitionConfirmationForm


class RefundConfirmationForm(forms.Form):
    title = _('Refund payment')


class FundingNeedsWorkForm(TransitionConfirmationForm):
    title = _('Funding needs work')

    custom_message = CustomMessageFormField(
        label=_('Custom message'),
        required=False,
        help_text=_('You can provide a custom message to the initiator explaining why the funding needs work.'),
    )

    def save(self, **kwargs):
        """
        Save the form data and return the custom message if provided.
        """
        if self.cleaned_data.get('custom_message'):
            self.transition.custom_message = self.cleaned_data['custom_message']
        return None


class FundingRejectedForm(TransitionConfirmationForm):
    title = _('Activity rejected')

    custom_message = CustomMessageFormField(
        label=_('Custom message'),
        required=False,
        help_text=_(
            'You can provide a custom message to the initiator explaining why their campaign was rejected.'),
    )

    def save(self, **kwargs):
        """
        Save the form data and return the custom message if provided.
        """
        if self.cleaned_data.get('custom_message'):
            self.transition.custom_message = self.cleaned_data['custom_message']
        return None


class FundingAcceptedForm(TransitionConfirmationForm):
    title = _('Crowdfunding campaign accepted')

    custom_message = CustomMessageFormField(
        label=_('Custom message'),
        required=False,
        help_text=_(
            'You can provide a custom message to the initiator to tell them their campaign was accepted and to tell them what the next steps will be..'),
    )

    def save(self, **kwargs):
        """
        Save the form data and return the custom message if provided.
        """
        if self.cleaned_data.get('custom_message'):
            self.transition.custom_message = self.cleaned_data['custom_message']
        return None
