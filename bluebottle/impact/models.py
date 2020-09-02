# -*- coding: utf-8 -*-
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatedFields

from bluebottle.utils.models import SortableTranslatableModel

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

    ('task', _('Task')),
    ('task-completed', _('Task completed')),
    ('event', _('Event')),
    ('event-completed', _('Event completed')),
    ('funding', _('Funding')),
    ('funding-completed', _('Funding completed')),

]


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
            _('Formulate the goal "Our goal is to..."'),
            max_length=100,
            help_text=_('E.g. "Save plastic" or "Reduce CO₂ emission"')
        ),
        text_with_target=models.CharField(
            _('Formulate the goal including the target “Our goal is to…”'),
            max_length=100,
            help_text=_(
                (
                    'E.g. “Save {} kg plastic” or “Reduce CO₂ emissions by {} liters”.'
                    'Make sure to add “{}” where the value should go.'
                )
            )
        ),
        text_passed=models.CharField(
            _('Formulate the result in past tense'),
            max_length=100,
            help_text=_('E.g. "Plastic saved" or "CO₂ emissions reduced"')
        ),
    )

    def __unicode__(self):
        return self.name

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super(ImpactType, self).save(**kwargs)

    class Meta:
        verbose_name = _('impact type')
        verbose_name_plural = _('impact types')


class ImpactGoal(models.Model):
    type = models.ForeignKey(
        ImpactType,
        verbose_name=_('type'),
        related_name='goals'
    )

    activity = models.ForeignKey(
        'activities.activity',
        verbose_name=_('activity'),
        related_name='goals'
    )

    target = models.FloatField(
        _('target'),
        help_text=_('Set a target for the impact you expect to make'),
        blank=False,
        null=True
    )

    realized = models.FloatField(
        _('realized'),
        help_text=_(
            'Enter your impact results here when the activity is finished'),
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _('impact goal')
        verbose_name_plural = _('impact goals')
