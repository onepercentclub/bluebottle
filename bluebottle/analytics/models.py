from django.db import models
from django.utils.translation import ugettext_lazy as _

from bluebottle.utils.models import BasePlatformSettings


class AnalyticsAdapter(models.Model):
    type = models.CharField(max_length=100, default='GoogleAnalytics')
    code = models.CharField(max_length=100, null=True, blank=True)
    analytics_settings = models.ForeignKey('analytics.AnalyticsPlatformSettings', related_name='adapters')


class AnalyticsPlatformSettings(BasePlatformSettings):

    class Meta:
        verbose_name_plural = _('analytics platform settings')
        verbose_name = _('analytics platform settings')
