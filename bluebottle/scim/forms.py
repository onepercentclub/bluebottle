from django import forms
from django.utils.translation import ugettext_lazy as _


class ResetTokenConfirmationForm(forms.Form):
    title = _('Reset token?!')
