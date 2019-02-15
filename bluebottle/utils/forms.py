from django import forms
from django.forms.models import ModelFormMetaclass

from django_fsm import FSMField


class FSMModelFormMetaCLass(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        if 'Meta' in attrs:
            for field in attrs['Meta'].model._meta.fields:
                if isinstance(field, FSMField):
                    attrs['{}_transition'.format(field.name)] = forms.ChoiceField(required=False)

        return super(FSMModelFormMetaCLass, cls).__new__(cls, name, bases, attrs)


class FSMModelForm(forms.ModelForm):
    __metaclass__ = FSMModelFormMetaCLass

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
