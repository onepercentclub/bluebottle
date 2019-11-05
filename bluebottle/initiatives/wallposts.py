from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.messages import (
    InitiativeWallpostOwnerMessage, InitiativeWallpostReactionMessage,
    InitiativeWallpostOwnerReactionMessage,
    InitiativeWallpostFollowerMessage
)

from bluebottle.wallposts.models import MediaWallpost, Wallpost, Reaction


@receiver(post_save, sender=MediaWallpost)
@receiver(post_save, sender=Wallpost)
def send_initiative_owner(sender, instance, created=False, *args, **kwargs):
    if created and isinstance(instance.content_object, Initiative):
        InitiativeWallpostOwnerMessage(instance).compose_and_send()


@receiver(post_save, sender=Reaction)
def send_reaction_initiative_owner(sender, instance, created=False, *args, **kwargs):
    if created and isinstance(instance.wallpost.content_object, Initiative):
        InitiativeWallpostReactionMessage(instance).compose_and_send()


@receiver(post_save, sender=Reaction)
def send_reaction_wallpost_owner(sender, instance, created=False, *args, **kwargs):
    if created and isinstance(instance.wallpost.content_object, Initiative):
        InitiativeWallpostOwnerReactionMessage(instance).compose_and_send()


@receiver(post_save, sender=MediaWallpost)
@receiver(post_save, sender=Wallpost)
def send_followers(sender, instance, created=False, *args, **kwargs):
    if created and isinstance(instance.content_object, Initiative) and instance.email_followers:
        InitiativeWallpostFollowerMessage(instance).compose_and_send()
