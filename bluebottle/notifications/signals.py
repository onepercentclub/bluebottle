from django.dispatch import receiver
from django_fsm import post_transition


@receiver(post_transition)
def transition_messages(sender, instance, name, source, target, **kwargs):

    if getattr(instance, 'send_messages', True):
        for message in getattr(instance, name).messages:
            message(instance).compose_and_send()
