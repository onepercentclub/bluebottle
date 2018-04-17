from __future__ import unicode_literals

from django.forms.widgets import ChoiceInput, CheckboxFieldRenderer, CheckboxSelectMultiple
from django.utils.html import format_html


class NiceCheckboxChoiceInput(ChoiceInput):
    input_type = 'checkbox'

    def render(self, name=None, value=None, attrs=None):
        if self.id_for_label:
            label_for = format_html(' for="{}"', self.id_for_label)
        else:
            label_for = ''
        attrs = dict(self.attrs, **attrs) if attrs else self.attrs
        return format_html(
            '{} <label{}>{}</label>', self.tag(attrs), label_for, self.choice_label
        )


class MultiCheckboxRenderer(CheckboxFieldRenderer):
    choice_input_class = NiceCheckboxChoiceInput


class CheckboxSelectMultipleWidget(CheckboxSelectMultiple):
    renderer = MultiCheckboxRenderer
