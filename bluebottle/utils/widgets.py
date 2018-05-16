from __future__ import unicode_literals

from urlparse import urlparse

from django.contrib.admin.widgets import AdminURLFieldWidget
from django.forms.widgets import CheckboxFieldRenderer, CheckboxSelectMultiple, CheckboxChoiceInput
from django.utils.html import format_html


class NiceCheckboxChoiceInput(CheckboxChoiceInput):

    def render(self, name=None, value=None, attrs=None):
        if self.id_for_label:
            label_for = format_html(' for="{}"', self.id_for_label)
        else:
            label_for = ''
        attrs = dict(self.attrs, **attrs) if attrs else self.attrs
        return format_html(
            '{} <label{}>{}</label>', self.tag(attrs), label_for, self.choice_label
        )

    def is_checked(self):
        return self.choice_value in self.value


class MultiCheckboxRenderer(CheckboxFieldRenderer):
    choice_input_class = NiceCheckboxChoiceInput


class CheckboxSelectMultipleWidget(CheckboxSelectMultiple):
    renderer = MultiCheckboxRenderer


class SecureAdminURLFieldWidget(AdminURLFieldWidget):
    def render(self, name, value, attrs=None):
        if urlparse(value).scheme not in ('http', 'https', ):
            return super(AdminURLFieldWidget, self).render(name, value, attrs)
        else:
            return super(SecureAdminURLFieldWidget, self).render(name, value, attrs)
