from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.timezone import now

from bluebottle.utils.utils import get_class

from .signals import *  # noqa


class Message(models.Model):

    recipient = models.ForeignKey('members.Member')
    sent = models.DateTimeField(null=True, blank=True)
    adapter = models.CharField(max_length=30, default='email')
    template = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    custom_message = models.TextField(blank=True, null=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def get_adapter(self):
        adapter_name = 'bluebottle.notifications.adapters.{}.{}MessageAdapter'.format(
            self.adapter,
            self.adapter.title()
        )
        return get_class(adapter_name)

    def send(self):
        adapter = self.get_adapter()(self)
        adapter.send()
        self.sent = now()
        self.save()
