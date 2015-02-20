from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_syncdb

from bluebottle.utils.utils import update_group_permissions
from .. import models


group_perms = {
    'Staff': {
        'perms': (
            'add_donation', 'change_donation', 'delete_donation',
        )
    }
}

@receiver(post_syncdb, sender=models)
def _update_permissions(sender, **kwargs):
    update_group_permissions(sender, group_perms)
