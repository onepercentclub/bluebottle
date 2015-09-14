
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import connection

from bluebottle.wallposts.models import MediaWallpost, TextWallpost

from bluebottle.common.tasks import _post_to_facebook


@receiver(post_save, sender=MediaWallpost)
@receiver(post_save, sender=TextWallpost)
def post_to_facebook(sender, instance, created, **kwargs):

    try:
        tenant = connection.tenant
    except AttributeError:
        tenant = None

    if created and instance.share_with_facebook:
        _post_to_facebook.delay(instance, tenant=tenant)
