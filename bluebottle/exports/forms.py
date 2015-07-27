from django import forms
from django.contrib.admin import widgets
from django.utils.translation import ugettext_lazy as _


class ExportDBForm(forms.Form):
    from_date = forms.DateField(label=_('from date'), widget=widgets.AdminDateWidget)
    to_date = forms.DateField(label=_('to date'), widget=widgets.AdminDateWidget)

    def clean(self):
        super(ExportDBForm, self).clean()
        frm, to = self.cleaned_data.get('from_date'), self.cleaned_data.get('to_date')
        if frm and to:
            if to < frm:
                raise forms.ValidationError(_('The to date must be later than the from date'))

            diff = to - frm
            import bpdb; bpdb.set_trace()
