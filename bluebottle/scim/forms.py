from django import forms
from django.utils.translation import gettext_lazy as _


class ResetTokenConfirmationForm(forms.Form):
    title = _('Reset token?!')
