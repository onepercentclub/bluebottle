from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html

from bluebottle.projects.models import ProjectDocument


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


class ProjectDocumentForm(forms.ModelForm):
    class Meta:
        model = ProjectDocument
        widgets = {
            'file': UploadWidget()
        }
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(ProjectDocumentForm, self).__init__(*args, **kwargs)
        self.fields['file'].required = False
