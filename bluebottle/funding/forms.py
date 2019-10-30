from django import forms
from django.utils.translation import ugettext_lazy as _


class RefundConfirmationForm(forms.Form):
    title = _('Refund payment')
