from builtins import object
from django.db import models
from django.utils.translation import ugettext_lazy as _

from bluebottle.utils.models import BasePlatformSettings


class AnalyticsPlatformSettings(BasePlatformSettings):
    fiscal_month_offset = models.PositiveIntegerField(
        _('Fiscal year offset'),
        help_text=_('This could be used in reporting.'),
        default=0)
    user_base = models.PositiveIntegerField(
        _("User base"),
        help_text=_('Number of employees or number of users that could access the platform.'),
        null=True,
        blank=True
    )

    class Meta(object):
        verbose_name_plural = _('reporting platform settings')
        verbose_name = _('reporting platform settings')
