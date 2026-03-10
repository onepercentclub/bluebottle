"""
Signal handlers for activity_pub lifecycle events (Start, Cancel, Delete, Finish) when
there is no LinkedActivity: apply the corresponding state transition to the adopted
activity (e.g. Deed) so synced activities still start/cancel/finish correctly.

Link handling lives in activity_links/signals.py; these handlers run only when no link
exists for the event.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from bluebottle.activity_links.models import LinkedActivity
from bluebottle.activity_pub.models import Cancel, Delete, Finish, Start

logger = logging.getLogger(__name__)


def _apply_to_adopted_if_no_link(event, transition_name):
    """If there is no LinkedActivity for this event, apply transition to adopted activity."""
    if LinkedActivity.objects.filter(event=event).exists():
        return
    adopted = event.adopted_activities.first()
    if adopted is None:
        return
    states = getattr(adopted, 'states', None)
    if states is None:
        return
    try:
        if transition_name == 'start':
            states.start(save=True)
        elif transition_name == 'cancel':
            states.cancel(save=True)
        elif transition_name == 'succeed':
            states.succeed(save=True)
    except Exception as e:
        logger.error(
            "Failed to apply activity_pub %s to adopted activity %s: %s",
            transition_name, adopted, e, exc_info=True
        )


@receiver(post_save, sender=Start)
def start_adopted(sender, instance, created, **kwargs):
    if not instance.is_local and created:
        _apply_to_adopted_if_no_link(instance.object, 'start')


@receiver(post_save, sender=Cancel)
def cancel_adopted(sender, instance, created, **kwargs):
    if not instance.is_local and created:
        _apply_to_adopted_if_no_link(instance.object, 'cancel')


@receiver(post_save, sender=Delete)
def delete_adopted(sender, instance, created, **kwargs):
    if not instance.is_local and created:
        # No link: transition adopted activity to cancelled (same as previous behaviour)
        _apply_to_adopted_if_no_link(instance.object, 'cancel')


@receiver(post_save, sender=Finish)
def finish_adopted(sender, instance, created, **kwargs):
    if not instance.is_local and created:
        _apply_to_adopted_if_no_link(instance.object, 'succeed')
