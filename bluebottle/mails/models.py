from builtins import object
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from bluebottle.utils.models import BasePlatformSettings
from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection


class MailPlatformSettings(BasePlatformSettings):
    email_logo = models.ImageField(
        null=True, blank=True, upload_to='site_content/',

        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]
    )

    address = models.CharField(
        null=True, blank=True, max_length=80
    )
    sender = models.CharField(
        null=True, blank=True, max_length=80
    )
    reply_to = models.CharField(
        null=True, blank=True, max_length=80
    )
    footer = models.TextField(
        null=True, blank=True
    )

    class Meta(object):
        verbose_name_plural = _('mail platform settings')
        verbose_name = _('mail platform settings')
