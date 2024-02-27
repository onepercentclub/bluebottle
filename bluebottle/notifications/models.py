from builtins import object

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from multiselectfield import MultiSelectField
from parler.models import TranslatableModel, TranslatedFields

from bluebottle.utils.models import BasePlatformSettings
from bluebottle.utils.utils import get_class


class Message(models.Model):
    recipient = models.ForeignKey('members.Member', on_delete=models.CASCADE)
    sent = models.DateTimeField(null=True, blank=True)
    adapter = models.CharField(max_length=30, default='email')
    template = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    body_html = models.TextField(blank=True, null=True)
    body_txt = models.TextField(blank=True, null=True)
    custom_message = models.TextField(blank=True, null=True)
    bcc = ArrayField(
        models.CharField(max_length=200, null=True),
        blank=True,
        null=True,
        default=list
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def get_adapter(self):
        adapter_name = 'bluebottle.notifications.adapters.{}.{}MessageAdapter'.format(
            self.adapter,
            self.adapter.title()
        )
        return get_class(adapter_name)

    def send(self, **context):
        adapter = self.get_adapter()(self)
        adapter.send(**context)
        self.sent = now()
        self.save()


class NotificationPlatformSettings(BasePlatformSettings):
    SHARE_OPTIONS = (
        ('twitter', _('Twitter')),
        ('facebook', _('Facebook')),
        ('facebookAtWork', _('Facebook at Work')),
        ('linkedin', _('LinkedIn')),
        ('whatsapp', _('Whatsapp')),
        ('yammer', _('Yammer')),
        ('teams', _('Teams')),
        ('email', _('Email')),
    )

    share_options = MultiSelectField(
        max_length=100, choices=SHARE_OPTIONS, blank=True
    )
    facebook_at_work_url = models.URLField(max_length=100, null=True, blank=True)
    default_yammer_group_id = models.CharField(max_length=100, null=True, blank=True)

    class Meta(object):
        verbose_name_plural = _('notification settings')
        verbose_name = _('notification settings')


class NotificationModelMixin(object):
    """
    This should be imported by models that need to trigger
    messages on change.
    """

    @classmethod
    def get_messages(cls, old, new):
        return []


class MessageTemplate(TranslatableModel):

    MESSAGES = (
        ('bluebottle.members.messages.AccountActivationMessage', _('Member activated')),
    )

    message = models.CharField(
        _('Message'), choices=MESSAGES,
        unique=True, max_length=500)

    translations = TranslatedFields(
        subject=models.CharField(_('Subject'), max_length=200),
        body_html=models.TextField(_('Body (html)'), blank=True),
        body_txt=models.TextField(_('Body (text)'), blank=True)
    )
