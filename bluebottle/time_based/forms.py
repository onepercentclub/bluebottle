from django import forms
from django.utils.translation import gettext_lazy as _

from bluebottle.utils.forms import TransitionConfirmationForm


class RegistrationRejectForm(TransitionConfirmationForm):
    title = _('Reject registration')

    custom_message = forms.CharField(
        widget=forms.Textarea,
        label=_('Custom message'),
        required=False,
        help_text=_(
            'You can provide a custom message for the applicant, '
            'this will replace the default rejection message.'
        ),
    )

    def save(self, **kwargs):
        """
        Save the form data and return the custom message if provided.
        """
        if self.cleaned_data.get('custom_message'):
            self.transition.custom_message = self.cleaned_data['custom_message']
        return None


class RegistrationAcceptForm(TransitionConfirmationForm):
    title = _('Accept registration')

    custom_message = forms.CharField(
        widget=forms.Textarea,
        label=_('Custom message'),
        required=False,
        help_text=_(
            'You can provide a custom message for the applicant, '
            'this will replace the default acceptance message.'
        ),
    )

    def save(self, **kwargs):
        """
        Save the form data and return the custom message if provided.
        """
        if self.cleaned_data.get('custom_message'):
            self.transition.custom_message = self.cleaned_data['custom_message']
        return None
