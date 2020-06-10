from django.utils.translation import ugettext_lazy as _
from django import forms
from django.core.urlresolvers import reverse
from django.forms.models import ModelFormMetaclass


class TransitionSelectWidget(forms.Select):
    template_name = 'admin/transitions.html'
    option_template_name = 'admin/transition_option.html'


class StateWidget(forms.TextInput):
    template_name = 'admin/state.html'


class StateMachineModelFormMetaClass(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        if 'Meta' in attrs:
            for field, machine in attrs['Meta'].model._state_machines.items():
                attrs[field] = forms.ChoiceField(
                    required=False,
                    widget=TransitionSelectWidget()
                )
                attrs[machine.field] = forms.CharField(
                    required=False,
                    widget=StateWidget()
                )

        return super(StateMachineModelFormMetaClass, cls).__new__(cls, name, bases, attrs)


class StateMachineModelForm(forms.ModelForm):
    __metaclass__ = StateMachineModelFormMetaClass

    def __init__(self, *args, **kwargs):
        super(StateMachineModelForm, self).__init__(*args, **kwargs)
        for field in self.state_machine_fields:
            manager = getattr(self.instance, field)
            transitions = manager.possible_transitions()

            self.fields[field].widget.attrs['obj'] = self.instance
            self.fields[field].label = _('Transitions')

            self.fields[manager.field].widget.attrs['state'] = manager.current_state

            def get_url(name):
                url_name = 'admin:{}_{}_state_transition'.format(
                    self.instance._meta.app_label,
                    self.instance._meta.model_name
                )
                return reverse(
                    url_name, args=(self.instance.pk, field, name)
                )
            self.fields[field].choices = [
                (get_url(transition.field), transition) for transition in transitions
                if not transition.automatic
            ]

    @property
    def state_machine_fields(self):
        return [field for field in self.instance._state_machines]
