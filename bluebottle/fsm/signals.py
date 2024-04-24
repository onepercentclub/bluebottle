from functools import partial

from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import CHANGE, LogEntry
from django.dispatch import receiver
from django.db import transaction

from django_tools.middlewares import ThreadLocal

from bluebottle.fsm.state import post_state_transition


@receiver(post_state_transition)
def transition_trigger(sender, instance, transition, **kwargs):
    request = ThreadLocal.get_current_request()
    transaction.on_commit(
        partial(
            LogEntry.objects.log_action,
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(
                instance, for_concrete_model=False
            ).pk,
            object_id=instance.pk,
            object_repr=str(instance),
            action_flag=CHANGE,
            change_message=f"Performed transition: {transition.name}",
        )
    )
