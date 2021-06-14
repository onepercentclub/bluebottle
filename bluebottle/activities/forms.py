from django import forms
from django.utils.translation import gettext_lazy as _


class ImpactReminderConfirmationForm(forms.Form):
    title = _('Send impact reminder message')
