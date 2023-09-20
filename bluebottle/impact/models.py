# -*- coding: utf-8 -*-
from builtins import object

from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _
from future.utils import python_2_unicode_compatible
from parler.models import TranslatedFields

from bluebottle.utils.models import SortableTranslatableModel, ValidatedModelMixin

ICONS = [
    ('people', _('People')),
    ('time', _('Time')),
    ('money', _('Money')),
    ('trees', _('Trees')),
    ('animals', _('Animals')),
    ('jobs', _('Jobs')),
    ('co2', _('C02')),
    ('water', _('Water')),
    ('plastic', _('plastic')),
    ('food', _('Food')),

    ('task', _('Task')),
    ('task-completed', _('Task completed')),
    ('event', _('Event')),
    ('event-completed', _('Event completed')),
    ('funding', _('Funding')),
    ('funding-completed', _('Funding completed')),

]


@python_2_unicode_compatible
class ImpactType(SortableTranslatableModel):
    slug = models.SlugField(
        _('slug'),
        max_length=100,
        unique=True,
        help_text=_('Do not change this field')
    )
    active = models.BooleanField(_('active'), default=True)

    icon = models.CharField(_('icon'), choices=ICONS,
                            null=True, blank=True, max_length=20)

    translations = TranslatedFields(
        name=models.CharField(
            _('name'),
            blank=True,
            max_length=100
        ),
        unit=models.CharField(
            _('unit'),
            blank=True,
            null=True,
            max_length=100,
            help_text=_('"l" or "kg". Leave this field blank if a unit is not applicable.')

        ),
        text=models.CharField(
            _(u'Formulate the goal "Our goal is to..."'),
            max_length=100,
            help_text=_(u'E.g. "Save plastic" or "Reduce CO₂ emission"')
        ),
        text_with_target=models.CharField(
            _(u'Formulate the goal including the target “Our goal is to…”'),
            max_length=100,
            help_text=_(
                (
                    u'E.g. “Save {} kg plastic” or “Reduce CO₂ emissions by {} liters”.'
                    u'Make sure to add “{}” where the value should go.'
                )
            )
        ),
        text_passed=models.CharField(
            _(u'Formulate the result in past tense'),
            max_length=100,
            help_text=_(u'E.g. "Plastic saved" or "CO₂ emissions reduced"')
        ),
    )

    def __str__(self):
        return self.name

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super(ImpactType, self).save(**kwargs)

    class Meta(object):
        ordering = ('id',)
        verbose_name = _('impact type')
        verbose_name_plural = _('impact types')


class ImpactGoal(ValidatedModelMixin, models.Model):
    type = models.ForeignKey(
        ImpactType,
        verbose_name=_('type'),
        related_name='goals',
        on_delete=models.CASCADE
    )

    activity = models.ForeignKey(
        'activities.activity',
        verbose_name=_('activity'),
        related_name='goals',
        on_delete=models.CASCADE
    )

    target = models.FloatField(
        _('target'),
        help_text=_('Set a target for the impact you expect to make'),
        blank=True,
        null=True
    )

    participant_impact = models.FloatField(
        _('impact per participant'),
        help_text=_('Mean impact each participants makes'),
        blank=True,
        null=True
    )

    @property
    def impact_realized(self):
        if self.realized:
            return self.realized
        if self.activity.succeeded_contributor_count:
            return self.activity.succeeded_contributor_count * self.participant_impact
        return self.realized_from_contributions

    realized_from_contributions = models.FloatField(
        _('realized from contributions'),
        blank=True,
        null=True
    )

    realized = models.FloatField(
        _('realized'),
        help_text=_(
            'Enter your impact results here when the activity is finished'),
        blank=True,
        null=True
    )

    class Meta(object):
        verbose_name = _('impact goal')
        verbose_name_plural = _('impact goals')

    @property
    def required_fields(self):
        from bluebottle.deeds.models import Deed

        if isinstance(self.activity, Deed):
            return ['target']

        return []

    def update(self):
        if (
            self.target and
            self.activity.enable_impact and
            self.activity.target and
            self.activity.realized
        ):
            amount = self.target / float(self.activity.target)

            self.realized_from_contributions = amount * float(self.activity.realized)
        else:
            self.realized_from_contributions = None
