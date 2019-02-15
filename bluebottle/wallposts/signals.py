
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import connection

from bluebottle.wallposts.models import MediaWallpost, TextWallpost, SystemWallpost

from bluebottle.common.tasks import _post_to_facebook


@receiver(post_save, sender=MediaWallpost)
@receiver(post_save, sender=TextWallpost)
def post_to_facebook(sender, instance, created, **kwargs):

    try:
        tenant = connection.tenant
    except AttributeError:
        tenant = None

    if created and instance.share_with_facebook:
        _post_to_facebook.apply_async(
            args=[instance],
            kwargs={'tenant': tenant},
            countdown=5
        )


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
