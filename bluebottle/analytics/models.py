from builtins import object
from django.db import models
from django.utils.translation import gettext_lazy as _

from djchoices.choices import DjangoChoices, ChoiceItem
from bluebottle.utils.fields import MoneyField

from bluebottle.utils.models import BasePlatformSettings


class AnalyticsPlatformSettings(BasePlatformSettings):
    class PlatformTypes(DjangoChoices):
        corporate = ChoiceItem('corporate', label=_('Corporate'))
        civic = ChoiceItem('civic', label=_('Civic'))
        society = ChoiceItem('society', label=_('Society'))

    user_base = models.PositiveIntegerField(
        _("Potential reach"),
        help_text=_('Total number of people who could potentially visit the platform (e.g. employees, citizens).'),
        null=True,
        blank=True
    )

    engagement_target = models.PositiveIntegerField(
        _("Contributor goal (people)"),
        help_text=_(
            'How many unique people do you want to engage this year through '
            'contributions like volunteering, donations, or good deeds?'
        ),
        null=True,
        blank=True
    )

    acts_of_impact_target = models.PositiveIntegerField(
        _("Contribution goal (actions)"),
        help_text=_(
            'How many total contributions do you aim to reach this year, regardless of how many people made them?'
        ),
        null=True,
        blank=True
    )

    hours_spent_target = models.PositiveIntegerField(
        _("Hours goal"),
        help_text=_(
            'How many total hours do you aim to spend on contributions this year.'
        ),
        null=True,
        blank=True
    )

    amount_raised_target = MoneyField(
        _("Donation goal"),
        help_text=_(
            'Total value of donations you aim to raise this year.'
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

    terminated = models.BooleanField(
        _("Terminated"),
        default=False,
        help_text=_('Is the platform terminated?')
    )

    class Meta(object):
        verbose_name_plural = _('reporting settings')
        verbose_name = _('reporting settings')
