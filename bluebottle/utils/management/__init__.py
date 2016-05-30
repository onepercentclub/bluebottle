from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_syncdb
from django.conf import settings

from bluebottle.utils.utils import update_group_permissions

"""
Connecting signal handler here for populating permissions.
This handler will work for any appname.models which defines
a GROUP_PERMS property.
TODO: Is this the correct place for a global signal handler.
"""

ADDITIONAL_GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_pictureitem', 'change_pictureitem', 'delete_pictureitem',
            'add_contenttype', 'change_contenttype', 'delete_contenttype',
            'add_oembeditem', 'change_oembeditem', 'delete_oembeditem',
            'add_rawhtmlitem', 'change_rawhtmlitem', 'delete_rawhtmlitem',
            'add_textitem', 'change_textitem', 'delete_textitem',
            'add_placeholder', 'change_placeholder', 'delete_placeholder',
            'add_contentitem', 'change_contentitem', 'delete_contentitem'
        )
    }
}


@receiver(post_syncdb)
def _update_permissions(sender, **kwargs):
    update_group_permissions(sender)

    # Load additional permissions after all models have been synced
    if kwargs['app'].__name__ == settings.INSTALLED_APPS[-1] + ".models":
        update_group_permissions(sender, ADDITIONAL_GROUP_PERMS)
