from django import forms
from django.forms.models import ModelFormMetaclass

from django_fsm import FSMField


class ButtonSelectWidget(forms.Select):
    template_name = 'admin/button_select.html'
    option_template_name = 'admin/button_select_option.html'


class FSMModelFormMetaClass(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        if 'Meta' in attrs:
            for field in attrs['Meta'].model._meta.fields:
                if isinstance(field, FSMField):
                    attrs['{}_transition'.format(field.name)] = forms.ChoiceField(
                        required=False,
                        widget=ButtonSelectWidget()
                    )

        return super(FSMModelFormMetaClass, cls).__new__(cls, name, bases, attrs)


class FSMModelForm(forms.ModelForm):
    __metaclass__ = FSMModelFormMetaClass

    def __init__(self, *args, **kwargs):
        super(FSMModelForm, self).__init__(*args, **kwargs)
        for fsm_field in self.fsm_fields:
            transitions = getattr(
                self.instance, 'get_available_{}_transitions'.format(fsm_field)
            )()
            choices = [
                (transition.name, transition.name) for transition in transitions
            ]
            self.fields[
                '{}_transition'.format(fsm_field)
            ].choices = [(None, '')] + choices

    def clean(self, *args, **kwargs):
        for field_name in self.fsm_fields:
            transition_name = self.cleaned_data.get('{}_transition'.format(field_name))
            if transition_name:
                getattr(self.instance, transition_name)()
        return super(FSMModelForm, self).clean(*args, **kwargs)

    @property
    def fsm_fields(self):
        return [field.name for field in self.instance._meta.fields if isinstance(field, FSMField)]
