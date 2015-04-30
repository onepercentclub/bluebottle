from django import forms
from django.utils.translation import ugettext as _

from .models import ProjectDocument


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
class ProjectDocumentForm(forms.ModelForm):
    class Meta:
        model = ProjectDocument
        widgets = {
            'file': UploadWidget()
        }

    def __init__(self, *args, **kwargs):
        super(ProjectDocumentForm, self).__init__(*args, **kwargs)
        self.fields['file'].required = False
