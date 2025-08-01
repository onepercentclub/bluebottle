from django import forms
from django.utils.translation import gettext_lazy as _

from bluebottle.utils.forms import TransitionConfirmationForm


class RefundConfirmationForm(forms.Form):
    title = _('Refund payment')


class FundingNeedsWorkForm(TransitionConfirmationForm):
    title = _('Funding needs work')

    custom_message = forms.CharField(
        widget=forms.Textarea,
        label=_('Custom message'),
        required=False,
        help_text=_('You can provide a custom message to the campaign owner explaining why the funding needs work.'),
    )

    def save(self, **kwargs):
        """
        Save the form data and return the custom message if provided.
        """
        if self.cleaned_data.get('custom_message'):
            self.transition.custom_message = self.cleaned_data['custom_message']
        return None
