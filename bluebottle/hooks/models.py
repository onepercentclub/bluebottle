from django.db import models
from django.utils import timezone

from django.core.management.utils import get_random_secret_key

from django.contrib.contenttypes.models import ContentType

from django.contrib.contenttypes import fields


class WebHook(models.Model):
    url = models.URLField()
    secret_key = models.CharField(max_length=50)

    def save(self, *args, **kwargs):
        if not self.secret_key:
            self.secret_key = get_random_secret_key()

        super().save(*args, **kwargs)


class SignalLog(models.Model):
    event = models.CharField(max_length=50)

    content_type = models.ForeignKey(ContentType, related_name='webhook_logs')
    instance_id = models.PositiveIntegerField()
    instance = fields.GenericForeignKey('content_type', 'instance_id')

    created = models.DateTimeField(default=timezone.now)


from bluebottle.hooks.signals import *  # noqa
