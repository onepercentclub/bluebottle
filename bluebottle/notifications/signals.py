from django.dispatch import receiver
from django_fsm import post_transition


@receiver(post_transition)
def transition_messages(sender, instance, name, source, target, **kwargs):

    if instance.send_messages:
        for message in getattr(instance, name).messages:
            message(instance).compose_and_send()
