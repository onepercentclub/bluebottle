from django.dispatch import receiver
from django.utils.timezone import now

from bluebottle.fsm import post_transition

from bluebottle.activities.models import Contribution, Activity


@receiver(post_transition)
def set_transition_date(sender, instance, transition, send_messages=True, message=None, **kwargs):
    if isinstance(instance, (Contribution, Activity)):
        instance.transition_date = now()
