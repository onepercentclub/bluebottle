import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from bluebottle.activity_links.models import LinkedActivity
from bluebottle.activity_pub.models import (
    AdoptionModeChoices, AdoptionTypeChoices, Publish, Update, Follow, Cancel,
    Finish, Delete
)

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Publish)
def link(sender, instance, created, **kwargs):
    try:
        if not instance.is_local and created:
            try:
                follow = Follow.objects.get(object=instance.actor)

                if (
                    follow.adoption_mode == AdoptionModeChoices.automatic or
                    LinkedActivity.object.filter(event=instance.object).exists()
                ) and follow.adoption_type == AdoptionTypeChoices.link:
                    instance.object.refresh_from_db()
                    LinkedActivity.objects.sync(instance.object)
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


@receiver(post_save, sender=Cancel)
def cancel(sender, instance, created, **kwargs):
    try:
        if not instance.is_local and created:
            link = LinkedActivity.objects.filter(event=instance.object).get()
            link.states.cancel(save=True)
    except Exception as e:
        logger.error(f"Failed to find link event: {str(e)}")


@receiver(post_save, sender=Delete)
def delete(sender, instance, created, **kwargs):
    try:
        if not instance.is_local and created:
            link = LinkedActivity.objects.filter(event=instance.object).get()
            link.delete()
    except Exception as e:
        logger.error(f"Failed to find link event: {str(e)}")


@receiver(post_save, sender=Finish)
def finish(sender, instance, created, **kwargs):
    try:
        if not instance.is_local and created:
            link = LinkedActivity.objects.filter(event=instance.object).get()
            link.states.succeed(save=True)
    except Exception as e:
        logger.error(f"Failed to find link event: {str(e)}")
