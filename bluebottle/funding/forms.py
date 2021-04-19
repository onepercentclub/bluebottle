from django import forms
from django.utils.translation import gettext_lazy as _


class RefundConfirmationForm(forms.Form):
    title = _('Refund payment')
