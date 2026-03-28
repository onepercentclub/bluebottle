"""
Signal handlers for activity_pub events (Create, Update, Start, Cancel, Delete, Finish).

Link-only: sync LinkedActivity and drive link state. When there is no LinkedActivity for
an event, adopted-activity state transitions (e.g. Deed.states.start) are handled in
activities/signals.py so that logic stays with the Activity/Deed models.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from bluebottle.activity_links.models import LinkedActivity
from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models import (
    Accept, AdoptionTypeChoices, Create, Delete, Finish, Follow,
    Cancel, Start, Update
)
from bluebottle.activity_pub.models import GoodDeed
from bluebottle.activity_pub.utils import get_platform_actor

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Create)
def link(sender, instance, created, **kwargs):
    try:
        if not instance.is_local and created:
            try:
                follow = Follow.objects.get(object=instance.actor)
                if follow.adoption_type == AdoptionTypeChoices.link:
                    instance.object.refresh_from_db()
                    LinkedActivity.objects.sync(instance.object)
                elif follow.adoption_type == AdoptionTypeChoices.sync:
                    instance.object.refresh_from_db()
                    if isinstance(instance.object, GoodDeed):
                        activity_type_in_auto = (
                            follow.automatic_adoption_activity_types and
                            'deed' in follow.automatic_adoption_activity_types
                        )
                        if activity_type_in_auto and not instance.object.adopted_activities.exists():
                            deed = adapter.adopt(instance.object)
                            Accept.objects.create(
                                actor=get_platform_actor(),
                                object=instance.object
                            )
            except Follow.DoesNotExist:
                logger.debug(f"No follow found for actor: {instance.actor}")
    except Exception as e:
        logger.error(f"Failed to auto-adopt event: {str(e)}")


@receiver(post_save, sender=Update)
def update(sender, instance, created, **kwargs):
    try:
        if not instance.is_local and created and hasattr(instance.object, 'linked_activity'):
            LinkedActivity.objects.sync(instance.object)
    except Exception as e:
        logger.error(f"Failed to find link event: {str(e)}")


@receiver(post_save, sender=Start)
def start(sender, instance, created, **kwargs):
    try:
        if not instance.is_local and created:
            try:
                link = LinkedActivity.objects.filter(event=instance.object).get()
                link.states.start(save=True)
            except LinkedActivity.DoesNotExist:
                pass  # Adopted-activity fallback is in activities/signals.py
    except Exception as e:
        logger.error(f"Failed to find link event: {str(e)}")


@receiver(post_save, sender=Cancel)
def cancel(sender, instance, created, **kwargs):
    try:
        if not instance.is_local and created:
            try:
                link = LinkedActivity.objects.filter(event=instance.object).get()
                link.states.cancel(save=True)
            except LinkedActivity.DoesNotExist:
                pass  # Adopted-activity fallback is in activities/signals.py
    except Exception as e:
        logger.error(f"Failed to find link event: {str(e)}")


@receiver(post_save, sender=Delete)
def delete(sender, instance, created, **kwargs):
    try:
        if not instance.is_local and created:
            try:
                link = LinkedActivity.objects.filter(event=instance.object).get()
                link.delete()
            except LinkedActivity.DoesNotExist:
                pass  # Adopted-activity fallback is in activities/signals.py
    except Exception as e:
        logger.error(f"Failed to find link event: {str(e)}")


@receiver(post_save, sender=Finish)
def finish(sender, instance, created, **kwargs):
    try:
        if not instance.is_local and created:
            try:
                link = LinkedActivity.objects.filter(event=instance.object).get()
                link.states.succeed(save=True)
            except LinkedActivity.DoesNotExist:
                pass  # Adopted-activity fallback is in activities/signals.py
    except Exception as e:
        logger.error(f"Failed to find link event: {str(e)}")
