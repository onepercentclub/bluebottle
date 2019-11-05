from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

from bluebottle.activities.models import Activity
from bluebottle.activities.messages import (
    ActivityWallpostOwnerMessage, ActivityWallpostReactionMessage,
    ActivityWallpostOwnerReactionMessage,
    ActivityWallpostFollowerMessage
)

from bluebottle.wallposts.models import MediaWallpost, Wallpost, Reaction


@receiver(post_save, sender=MediaWallpost)
@receiver(post_save, sender=Wallpost)
def send_activity_owner(sender, instance, created=False, *args, **kwargs):
    if created and isinstance(instance.content_object, Activity):
        ActivityWallpostOwnerMessage(instance).compose_and_send()


@receiver(post_save, sender=Reaction)
def send_reaction_activity_owner(sender, instance, created=False, *args, **kwargs):
    if created and isinstance(instance.wallpost.content_object, Activity):
        ActivityWallpostReactionMessage(instance).compose_and_send()


@receiver(post_save, sender=Reaction)
def send_reaction_wallpost_owner(sender, instance, created=False, *args, **kwargs):
    if created and isinstance(instance.wallpost.content_object, Activity):
        ActivityWallpostOwnerReactionMessage(instance).compose_and_send()


@receiver(post_save, sender=MediaWallpost)
@receiver(post_save, sender=Wallpost)
def send_followers(sender, instance, created=False, *args, **kwargs):
    if created and isinstance(instance.content_object, Activity) and instance.email_followers:
        ActivityWallpostFollowerMessage(instance).compose_and_send()
