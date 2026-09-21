from builtins import object
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models
from django.utils.translation import gettext_lazy as _

from bluebottle.utils.models import BasePlatformSettings
from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection


def validate_sender_is_not_email(value):
    if not value or not value.strip():
        return
    try:
        validate_email(value.strip())
    except ValidationError:
        return
    raise ValidationError(
        _('Enter a display name, not an email address.')
    )


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
        null=True, blank=True, max_length=80,
        help_text=_('Email address used as the From address for platform emails.')
    )
    sender = models.CharField(
        null=True, blank=True, max_length=80,
        help_text=_(
            'Name shown next to the From address, such as the platform name. '
            'Do not use an email address.'
        ),
        validators=[validate_sender_is_not_email],
    )
    reply_to = models.CharField(
        null=True, blank=True, max_length=80,
        help_text=_('Email address used when recipients reply to a platform email.')
    )
    footer = models.TextField(
        null=True, blank=True,
        help_text=_('Optional text added at the bottom of platform emails.')
    )

    class Meta(object):
        verbose_name_plural = _('mail platform settings')
        verbose_name = _('mail platform settings')
