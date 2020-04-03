from django import forms
from django.utils.translation import ugettext_lazy as _


class LoginAsConfirmationForm(forms.Form):
    title = _('Login as')


class SendPasswordResetMailConfirmationForm(forms.Form):
    title = _('Send password reset mail')


class SendWelcomeMailConfirmationForm(forms.Form):
    title = _('Send welcome email')
