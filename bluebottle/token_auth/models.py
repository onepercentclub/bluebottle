from django.conf import settings
from django.db import models


class CheckedToken(models.Model):
    """
    Stores the used tokens for safety-checking purposes.
    """
    token = models.CharField(max_length=300)
    timestamp = models.DateTimeField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    class Meta:
        ordering = ('-timestamp', 'user__username')

    def __unicode__(self):
        return '{0} - {1}, {2}'.format(
            self.token, self.timestamp, self.user.username)
