from builtins import object
from django.conf import settings
from django.db import models
from future.utils import python_2_unicode_compatible

from djchoices.choices import DjangoChoices, ChoiceItem


@python_2_unicode_compatible
class CheckedToken(models.Model):
    """
    Stores the used tokens for safety-checking purposes.
    """
    token = models.CharField(max_length=300)
    timestamp = models.DateTimeField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta(object):
        ordering = ('-timestamp', 'user__username')

    def __str__(self):
        return '{0} - {1}, {2}'.format(
            self.token, self.timestamp, self.user.username)


class SAMLLog(models.Model):
    body = models.TextField()
    created = models.DateTimeField(auto_now=True)

    @classmethod
    def log(
        cls,
        body,
    ):
        return cls.objects.create(
            body=body,
        )
