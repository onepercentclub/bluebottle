from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from multiselectfield import MultiSelectField

from bluebottle.utils.models import BasePlatformSettings
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


class NotificationPlatformSettings(BasePlatformSettings):
    MATCH_OPTIONS = (
        ('theme', _('Theme')),
        ('skill', _('Skill')),
        ('location', _('Location')),
    )

    SHARE_OPTIONS = (
        ('twitter', _('Twitter')),
        ('facebook', _('Facebook')),
        ('facebookAtWork', _('Facebook at Work')),
        ('linkedin', _('LinkedIn')),
        ('whatsapp', _('Whatsapp')),
        ('yammer', _('Yammer')),
        ('email', _('Email')),
    )

    share_options = MultiSelectField(
        max_length=100, choices=SHARE_OPTIONS, blank=True
    )
    facebook_at_work_url = models.URLField(max_length=100, null=True, blank=True)

    match_options = MultiSelectField(
        max_length=100, choices=MATCH_OPTIONS, blank=True
    )

    class Meta:
        verbose_name_plural = _('notification settings')
        verbose_name = _('notification settings')
