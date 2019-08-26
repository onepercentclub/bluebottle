from django import forms
from django.forms import CheckboxInput
from django.forms.models import ModelFormMetaclass
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.models import Activity


class ButtonSelectWidget(forms.Select):
    template_name = 'admin/button_select.html'
    option_template_name = 'admin/button_select_option.html'


class FSMModelFormMetaClass(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        if 'Meta' in attrs:
            for transition in attrs['Meta'].model._transitions:
                attrs[transition[0]] = forms.ChoiceField(
                    required=False,
                    widget=ButtonSelectWidget()
                )

        return super(FSMModelFormMetaClass, cls).__new__(cls, name, bases, attrs)


class FSMModelForm(forms.ModelForm):
    __metaclass__ = FSMModelFormMetaClass

    def __init__(self, *args, **kwargs):
        super(FSMModelForm, self).__init__(*args, **kwargs)
        for fsm_field in self.fsm_fields:
            transitions = getattr(self.instance, fsm_field).all_transitions
            self.fields[fsm_field].widget.attrs['obj'] = self.instance
            self.fields[fsm_field].choices = [
                (transition.name, transition.name) for transition in transitions
            ]
            if isinstance(self.instance, Activity):
                # Default polymorphic activities to base activity
                self.fields[fsm_field].widget.attrs['action_url'] = 'admin:activities_activity_transition'
            else:
                self.fields[fsm_field].widget.attrs['action_url'] = 'admin:{}_{}_transition'.format(
                    self.instance._meta.app_label,
                    self.instance._meta.model_name
                )

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
    send_messages = forms.BooleanField(
        initial=True,
        required=False,
        widget=CheckboxInput,
        label=_('Send messages'),
        help_text=_('Should messages be send or should we transition without notifying users?')
    )
