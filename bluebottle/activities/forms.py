from django import forms
from django.utils.translation import ugettext_lazy as _


class ImpactReminderConfirmationForm(forms.Form):
    title = _('Send impact reminder message')
