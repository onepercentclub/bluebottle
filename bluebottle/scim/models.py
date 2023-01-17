from builtins import object
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from bluebottle.segments.models import SegmentType
from bluebottle.utils.models import BasePlatformSettings
from bluebottle.scim.utils import SCIMPath


class SCIMPlatformSettings(BasePlatformSettings):
    bearer_token = models.CharField(_('Bearer Token'), max_length=32)

    @property
    def segments(self):
        return (
            (SCIMPath(setting.path), setting.segment_type)
            for setting in self.segment_settings.all()
        )

    def save(self, *args, **kwargs):
        if not self.bearer_token:
            self.bearer_token = get_random_string(32)

        super(SCIMPlatformSettings, self).save(*args, **kwargs)

    class Meta(object):
        verbose_name_plural = _('scim platform settings')
        verbose_name = _('scim platform settings')


class SCIMSegmentSetting(models.Model):
    settings = models.ForeignKey(SCIMPlatformSettings, on_delete=models.CASCADE, related_name='segment_settings')
    path = models.CharField(max_length=200)
    segment_type = models.ForeignKey(SegmentType, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.settings = SCIMPlatformSettings.objects.get()
        return super().save(*args, **kwargs)
