
from django.db.models.signals import post_save
from django.dispatch import receiver

from bluebottle.wallposts.models import MediaWallpost, TextWallpost, SystemWallpost


@receiver(post_save, sender=TextWallpost)
def clean_up_system_wallpost(sender, instance, created, **kwargs):

    # Remove SystemWallpost connected to the same donation
    if instance.donation:
        SystemWallpost.objects.filter(donation=instance.donation).all().delete()


@receiver(post_save, sender=MediaWallpost)
def pin_owner_wallpost(sender, instance, created, **kwargs):
    """
    Make sure we pin the media wallpost if it is the latest project/task owner.
    And unpin others.
    """
    if not instance.pinned:
        owner = instance.content_object.owner
        latest = MediaWallpost.objects.filter(
            object_id=instance.object_id,
            content_type=instance.content_type,
            author=owner
        ).order_by('-created').first()
        if latest and instance == latest:
            MediaWallpost.objects.filter(
                object_id=instance.object_id,
                content_type=instance.content_type,
                author=owner,
                pinned=True
            ).update(pinned=False)
            latest.pinned = True
            latest.save()
