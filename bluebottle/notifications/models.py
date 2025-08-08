from builtins import object

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from multiselectfield import MultiSelectField
from parler.models import TranslatableModel, TranslatedFields

from django_quill.fields import QuillField

from bluebottle.utils.models import BasePlatformSettings
from bluebottle.utils.utils import get_class


class Message(models.Model):
    recipient = models.ForeignKey('members.Member', on_delete=models.CASCADE)
    sent = models.DateTimeField(null=True, blank=True)
    adapter = models.CharField(max_length=30, default='email')
    template = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    body_html = models.TextField(blank=True, null=True)
    insert_method = models.CharField(max_length=10, default='append')
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
        (
            'bluebottle.members.messages.AccountActivationMessage',
            _('Member activated')
        ),
        (
            'bluebottle.grant_management.messages.activity_manager.GrantApplicationApprovedMessage',
            _('Grant application approved')
        ),
    )

    message = models.CharField(
        _('Mail'), choices=MESSAGES,
        unique=True, max_length=500)

    INSERT_METHODS = (
        ('replace', _('Replace the entire message')),
        ('append', _('Append this to the original message')),
    )

    insert_method = models.CharField(
        _('Insert method'),
        max_length=20,
        choices=INSERT_METHODS,
        default='append'
    )

    translations = TranslatedFields(
        subject=models.CharField(_('Subject'), max_length=200),
        body_html=QuillField(_('Message'), blank=True),
    )
