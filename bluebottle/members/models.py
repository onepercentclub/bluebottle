from django.conf import settings
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
    pass


class CheckedToken(models.Model):
    """
    Stores the used tokens for safety-checking purposes.
    """
    token = models.CharField(max_length=300)
    timestamp = models.DateTimeField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    class Meta:
        ordering = ('timestamp', 'user__username')

    def __unicode__(self):
        return '{0} - {1}, {2}'.format(
            self.token, self.timestamp, self.user.username)
