from django.dispatch import receiver
from django_fsm import post_transition


@receiver(post_transition)
def transition_messages(sender, instance, **kwargs):
    # Only try to send messages if we have a 'name' and 'send_messages' is not False.
    if hasattr(kwargs, 'name') and getattr(instance, 'send_messages', True):
        for message in getattr(instance, kwargs['name']).messages:
            message(instance).compose_and_send()
