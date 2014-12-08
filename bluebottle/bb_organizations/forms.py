from django import forms
from django.utils.translation import ugettext as _
from django.utils.html import format_html

from bluebottle.utils.model_dispatcher import get_organizationdocument_model

DOCUMENT_MODEL = get_organizationdocument_model()

# Widgets
class UploadWidget(forms.FileInput):
    def render(self, name, value, attrs=None):
        html = super(UploadWidget, self).render(name, value, attrs)
        if value:
            text = _('Change:')
        else:
            text = _('Add:')

        html = format_html(
            '<p class="url">{0} {1}</p>',
            text, html
        )
        return html


# Forms
class OrganizationDocumentForm(forms.ModelForm):
    class Meta:
        model = DOCUMENT_MODEL
        widgets = {
            'file': UploadWidget()
        }

    def __init__(self, *args, **kwargs):
        super(OrganizationDocumentForm, self).__init__(*args, **kwargs)
        self.fields['file'].required = False
