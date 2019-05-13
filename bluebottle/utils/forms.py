from django import forms
from django.forms import CheckboxInput
from django.forms.models import ModelFormMetaclass
from django.utils.translation import ugettext_lazy as _

from django_fsm import FSMField

from bluebottle.activities.models import Activity


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
            field_name = '{}_transition'.format(fsm_field)
            self.fields[field_name].choices = [
                (transition.name, transition.name) for transition in transitions
            ]
            self.fields[field_name].widget.attrs['obj'] = self.instance
            if isinstance(self.instance, Activity):
                # Catch polymorphic activity
                self.fields[field_name].widget.attrs['action_url'] = 'admin:activities_activity_transition'
            else:
                self.fields[field_name].widget.attrs['action_url'] = 'admin:{}_{}_transition'.format(
                    self.instance._meta.app_label,
                    self.instance._meta.model_name
                )

    def clean(self, *args, **kwargs):
        for field_name in self.fsm_fields:
            transition_name = self.cleaned_data.get('{}_transition'.format(field_name))
            if transition_name:
                getattr(self.instance, transition_name)()
        return super(FSMModelForm, self).clean(*args, **kwargs)

    @property
    def fsm_fields(self):
        return [field.name for field in self.instance._meta.fields if isinstance(field, FSMField)]


class TransitionConfirmationForm(forms.Form):
    title = _('Transition')
    send_messages = forms.BooleanField(
        initial=True,
        required=False,
        widget=CheckboxInput,
        label=_('Send messages'),
        help_text=_('Should messages be send or should we transition without notifying users?')
    )
