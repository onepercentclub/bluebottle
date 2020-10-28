from django.conf import settings
from django.db import models
from future.utils import python_2_unicode_compatible


@python_2_unicode_compatible
class CheckedToken(models.Model):
    """
    Stores the used tokens for safety-checking purposes.
    """
    token = models.CharField(max_length=300)
    timestamp = models.DateTimeField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    class Meta:
        ordering = ('-timestamp', 'user__username')

    def __str__(self):
        return '{} - {}, {}'.format(
            self.token, self.timestamp, self.user.username)
