from django.dispatch import receiver

from bluebottle.fsm import post_transition
from bluebottle.follow.models import follow, unfollow


@receiver(post_transition)
def transition_messages(sender, instance, transition, **kwargs):
    should_follow = transition.options.get('follow')

    # Only try to send messages if 'send_messages' is not False.
    if should_follow is False:
        unfollow(instance.user, instance.activity)

    if should_follow is True:
        follow(instance.user, instance.activity)
