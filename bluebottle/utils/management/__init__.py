from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_syncdb

from bluebottle.utils.utils import update_group_permissions

"""
Connecting signal handler here for populating permissions.
This handler will work for any appname.models which defines 
a GROUP_PERMS property. 
TODO: Is this the correct place for a global signal handler.
"""
@receiver(post_syncdb)
def _update_permissions(sender, **kwargs):
    update_group_permissions(sender)
