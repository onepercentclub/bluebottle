from django.dispatch import receiver

from bluebottle.fsm import post_transition


@receiver(post_transition)
def transition_messages(sender, instance, transition, signal=None, send_messages=True, **options):
    # Only try to send messages if 'send_messages' is not False.
    if send_messages:
        for msg in transition.options.get('messages', []):
            msg(instance, **options).compose_and_send()
