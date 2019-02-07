from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _

from bluebottle.utils.models import BasePlatformSettings


class SCIMPlatformSettings(BasePlatformSettings):
    bearer_token = models.CharField(_('Bearer Token'), max_length=32)

    def save(self, *args, **kwargs):
        if not self.bearer_token:
            self.bearer_token = get_random_string(32)

        super(SCIMPlatformSettings, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = _('scim platform settings')
        verbose_name = _('scim platform settings')
