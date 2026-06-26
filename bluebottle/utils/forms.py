from django import forms
from django.forms.models import ModelFormMetaclass
from django.template.defaultfilters import linebreaks
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _
from django_quill.forms import QuillFormField
from django_quill.quill import Quill, QuillParseError
from django_quill.widgets import QuillWidget
from future.utils import with_metaclass

from bluebottle.utils.utils import clean_html


class CustomMessageFormField(QuillFormField):

    def __init__(self, *args, **kwargs):
        kwargs['widget'] = QuillWidget(config_name='custom_message')
        super(QuillFormField, self).__init__(*args, **kwargs)

    def clean(self, value):
        value = super(QuillFormField, self).clean(value)
        if not value:
            return ''
        try:
            html = Quill(value).html
        except QuillParseError:
            html = linebreaks(escape(value))
        return clean_html(html or '')


class ButtonSelectWidget(forms.Select):
    template_name = 'admin/button_select.html'
    option_template_name = 'admin/button_select_option.html'


class FSMModelFormMetaClass(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        if 'Meta' in attrs and False:
            for transition in attrs['Meta'].model._transitions:
                attrs[transition[0]] = forms.ChoiceField(
                    required=False,
                    widget=ButtonSelectWidget()
                )

        return super(FSMModelFormMetaClass, cls).__new__(cls, name, bases, attrs)


class FSMModelForm(with_metaclass(FSMModelFormMetaClass, forms.ModelForm)):
    def __init__(self, *args, **kwargs):
        super(FSMModelForm, self).__init__(*args, **kwargs)
        for fsm_field in self.fsm_fields:
            transitions = getattr(self.instance, fsm_field).all_transitions
            self.fields[fsm_field].widget.attrs['obj'] = self.instance

            def get_url(name):
                url_name = 'admin:{}_{}_transition'.format(
                    self.instance._meta.app_label,
                    self.instance._meta.model_name
                )
                return reverse(
                    url_name, args=(self.instance.pk, fsm_field, name)
                )

            self.fields[fsm_field].choices = [
                (get_url(transition.name), transition.name) for transition in transitions
                if not transition.options.get('automatic')
            ]

    def clean(self, *args, **kwargs):
        for field_name in self.fsm_fields:
            transition_name = self.cleaned_data.get(field_name)
            if transition_name:
                getattr(getattr(self.instance, field_name), transition_name)()
        return super(FSMModelForm, self).clean(*args, **kwargs)

    @property
    def fsm_fields(self):
        return [trans[0] for trans in self.instance._transitions]


class TransitionConfirmationForm(forms.Form):
    title = _('Transition')
    include_custom_message = None
    send_messages = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'checked': True}),
        label=_('Send messages'),
        help_text=_('Should messages be send or should we transition without notifying users?')
    )

    @classmethod
    def resolve_message_class(cls):
        message_class = getattr(cls, 'message_class', None)
        if message_class is None:
            return None
        if isinstance(message_class, type):
            return message_class
        return message_class()

    @classmethod
    def use_custom_message(cls):
        if cls.include_custom_message is False:
            return False
        if cls.include_custom_message is True:
            return True
        return cls.resolve_message_class() is not None

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop("instance", None)
        self.transition = kwargs.pop("transition", None)
        super().__init__(*args, **kwargs)

        if self.use_custom_message() and 'custom_message' not in self.fields:
            self.fields['custom_message'] = CustomMessageFormField(
                label=_('Email message'),
                required=False,
            )

        message_class = self.resolve_message_class()
        if (
            message_class
            and self.instance
            and not self.is_bound
            and 'custom_message' in self.fields
            and 'custom_message' not in self.initial
        ):
            message = message_class(self.instance)
            self.fields['custom_message'].initial = message.get_message_block_html()

    def save(self, **kwargs):
        if self.cleaned_data.get('custom_message'):
            self.transition.custom_message = self.cleaned_data['custom_message']
        return None
