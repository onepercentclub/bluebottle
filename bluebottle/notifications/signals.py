from django.dispatch import receiver

from bluebottle.fsm import post_transition


@receiver(post_transition)
def transition_messages(sender, instance, transition, send_messages=True, message=None, **kwargs):
    # Only try to send messages if 'send_messages' is not False.
    if send_messages:
        for msg in transition.options.get('messages', []):
            msg(instance).compose_and_send()
