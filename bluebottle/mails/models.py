from django.db import models
from django.utils.translation import ugettext_lazy as _

from bluebottle.utils.models import BasePlatformSettings


class MailPlatformSettings(BasePlatformSettings):
    email_logo = models.ImageField(null=True, blank=True, upload_to='site_content/')

    class Meta:
        verbose_name_plural = _('mail platform settings')
        verbose_name = _('mail platform settings')
