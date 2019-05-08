from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.forms.models import model_to_dict

from django_fsm import pre_transition, post_transition


@receiver(pre_transition)
def validate_transition_form(sender, instance, name, method_kwargs, **kwargs):
    transition = method_kwargs['transition']

    if transition.form:
        form = transition.form(data=model_to_dict(instance))
        if form.errors:
            raise ValidationError(form.errors)


@receiver(post_transition)
def transition_messages(sender, instance, name, method_kwargs, **kwargs):
    # Only try to send messages if 'send_messages' is not False.
    transition = method_kwargs['transition']
    if method_kwargs.get('send_messages'):
        for message in getattr(transition, 'messages', []):
            message(instance).compose_and_send()
