from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.forms.models import model_to_dict

from django_fsm import pre_transition, post_transition


@receiver(pre_transition)
def validate_transition_form(sender, instance, name=None, method_kwargs=None, **kwargs):
    if not method_kwargs:
        return

    transition = method_kwargs['transition']

    if transition.form:
        form = transition.form(data=model_to_dict(instance))
        if form.errors:
            raise ValidationError(
                dict(
                    (form.fields[field].label, errors)
                    for field, errors in form.errors.items()
                )
            )


@receiver(post_transition)
def transition_messages(sender, instance, name=None, method_kwargs=None, **kwargs):
    if not method_kwargs:
        return

    # Only try to send messages if 'send_messages' is not False.
    transition = method_kwargs['transition']
    if method_kwargs.get('send_messages'):
        for message in getattr(transition, 'messages', []):
            message(instance).compose_and_send()
