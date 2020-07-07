from django import forms
from django.utils.translation import ugettext_lazy as _


class SetPermissionsConfirmationForm(forms.Form):
    title = _('Set CMS permissions')


class ClearPermissionsConfirmationForm(forms.Form):
    title = _('Clear CMS permissions')
