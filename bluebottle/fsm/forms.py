from django.forms import Select
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.core.urlresolvers import reverse
from django.forms.models import ModelFormMetaclass
from future.utils import with_metaclass


class TransitionSelectWidget(forms.Select):
    template_name = 'admin/transitions.html'
    option_template_name = 'admin/transition_option.html'


class StateWidget(forms.TextInput):
    template_name = 'admin/state.html'


class StateMachineModelFormMetaClass(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        if 'Meta' in attrs:
            for field, machine in list(attrs['Meta'].model._state_machines.items()):
                attrs[field] = forms.ChoiceField(
                    required=False,
                    widget=TransitionSelectWidget()
                )
                attrs[machine.field] = forms.CharField(
                    required=False,
                    widget=StateWidget()
                )

                # Create a sto force setting state by super users
                force_name = "force_{}".format(machine.field)
                attrs[force_name] = forms.ChoiceField(
                    required=False,
                    choices=[(None, '---')] + [(s.value, s.name) for s in list(machine.states.values())],
                    widget=Select(),
                    help_text=_("Careful! This will change the status without triggering any side effects!")
                )
        return super(StateMachineModelFormMetaClass, cls).__new__(cls, name, bases, attrs)


class StateMachineModelForm(with_metaclass(StateMachineModelFormMetaClass, forms.ModelForm)):
    def __init__(self, *args, **kwargs):
        super(StateMachineModelForm, self).__init__(*args, **kwargs)
        for field in self.state_machine_fields:
            machine = getattr(self.instance, field)
            transitions = machine.possible_transitions()

            self.fields[field].widget.attrs['obj'] = self.instance
            self.fields[field].label = _('Transitions')

            self.fields[machine.field].widget.attrs['state'] = machine.current_state

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
                if not transition.automatic and not transition.options.get('hide_from_admin')
            ]
            force_field = "force_{}".format(machine.field)
            if machine.current_state:
                self.fields[force_field].initial = machine.current_state.value

    def save(self, commit=True):
        for field in self.data:
            if field.startswith('force_'):
                force_data = field.replace('force_', '')
                if hasattr(self, 'cleaned_data') and self.cleaned_data[field]:
                    setattr(self.instance, force_data, self.cleaned_data[field])
        return super(StateMachineModelForm, self).save(commit=commit)

    @property
    def state_machine_fields(self):
        return [field for field in self.instance._state_machines]
