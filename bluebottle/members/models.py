from django.utils.translation import ugettext_lazy as _
from django.db import models
from bluebottle.bb_accounts.models import BlueBottleBaseUser

GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_member', 'change_member', 'delete_member',
        )
    }
}


class Member(BlueBottleBaseUser):
    remote_id = models.CharField(_('remote_id'),
                                 max_length=75,
                                 blank=True,
                                 null=True)
