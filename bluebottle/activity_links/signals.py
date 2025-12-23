import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from bluebottle.activity_links.models import LinkedActivity
from bluebottle.activity_pub.models import AdoptionModeChoices, AdoptionTypeChoices, Publish, Update, Follow

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Publish)
@receiver(post_save, sender=Update)
def update_event(sender, instance, created, **kwargs):
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
