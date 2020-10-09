from django import forms
from django.core.urlresolvers import reverse
from django.forms.models import ModelFormMetaclass
from django.utils.translation import ugettext_lazy as _
from future.utils import with_metaclass


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
    send_messages = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'checked': True}),
        label=_('Send messages'),
        help_text=_('Should messages be send or should we transition without notifying users?')
    )
