from builtins import object
from django.db import models
from django.utils.translation import ugettext_lazy as _

from djchoices.choices import DjangoChoices, ChoiceItem

from bluebottle.utils.models import BasePlatformSettings


class AnalyticsPlatformSettings(BasePlatformSettings):
    class PlatformTypes(DjangoChoices):
        corporate = ChoiceItem('corporate', label=_('Corporate'))
        programs = ChoiceItem('programs', label=_('Programs'))
        civic = ChoiceItem('civic', label=_('Civic'))

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

    platform_type = models.CharField(
        _("platform type"),
        choices=PlatformTypes.choices,
        default='corporate',
        max_length=10
    )

    class Meta(object):
        verbose_name_plural = _('reporting platform settings')
        verbose_name = _('reporting platform settings')
