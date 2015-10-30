from django import forms
from django.conf import settings
from django.contrib.admin import widgets
from django.utils.translation import ugettext_lazy as _


class ExportDBForm(forms.Form):
    from_date = forms.DateField(label=_('from date'),
                                widget=widgets.AdminDateWidget)
    to_date = forms.DateField(label=_('to date'),
                              widget=widgets.AdminDateWidget)

    def clean(self):
        cleaned_data = super(ExportDBForm, self).clean()
        frm, to = cleaned_data.get('from_date'), cleaned_data.get('to_date')
        if frm and to:
            if to < frm:
                raise forms.ValidationError(
                    _('The to date must be later than the from date'))

            diff = to - frm
            if diff.days > settings.EXPORT_MAX_DAYS:
                raise forms.ValidationError(
                    _(
                        'The delta between from and to date is limited to %d days') % settings.EXPORT_MAX_DAYS
                )
        return cleaned_data
