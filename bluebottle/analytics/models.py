from builtins import object
from django.db import models
from django.utils.translation import gettext_lazy as _

from djchoices.choices import DjangoChoices, ChoiceItem

from bluebottle.utils.models import BasePlatformSettings


class AnalyticsPlatformSettings(BasePlatformSettings):
    class PlatformTypes(DjangoChoices):
        corporate = ChoiceItem('corporate', label=_('Corporate'))
        programs = ChoiceItem('programs', label=_('Programs'))
        civic = ChoiceItem('civic', label=_('Civic'))

    user_base = models.PositiveIntegerField(
        _("User base"),
        help_text=_('Number of employees or number of users that could access the platform.'),
        null=True,
        blank=True
    )
    engagement_target = models.PositiveIntegerField(
        _("Engagement"),
        help_text=_(
            'Target for the number of people contributing to an activity or starting an activity per year.'
        ),
        null=True,
        blank=True
    )

    platform_type = models.CharField(
        _("platform type"),
        choices=PlatformTypes.choices,
        default='corporate',
        max_length=10
    )

    plausible_embed_link = models.CharField(
        _("Plausibe embed link"), null=True, blank=True, max_length=256
    )

    class Meta(object):
        verbose_name_plural = _('reporting platform settings')
        verbose_name = _('reporting platform settings')
