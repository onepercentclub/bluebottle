from django.dispatch import receiver

from bluebottle.fsm import post_transition


@receiver(post_transition)
def transition_messages(sender, instance, name=None, options=None, send_messages=None, **kwargs):
    # Only try to send messages if 'send_messages' is not False.
    if send_messages:
        for message in options.get('messages', []):
            message(instance).compose_and_send()
