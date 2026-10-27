from builtins import object

from django.db import models
from django.utils.translation import gettext_lazy as _
from djchoices import DjangoChoices, ChoiceItem


class OfficeRegion(models.Model):
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)

    class Meta(object):
        ordering = ['name']
        verbose_name = _('Work location region')
        verbose_name_plural = _('Work location regions')

    def __str__(self):
        return self.name

    class JSONAPIMeta(object):
        resource_name = 'offices/regions'


class OfficeSubRegion(models.Model):
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    region = models.ForeignKey(
        'offices.OfficeRegion',
        verbose_name=_('Work location region'),
        null=True, blank=True,
        on_delete=models.CASCADE)

    class Meta(object):
        ordering = ['name']
        verbose_name = _('Work location group')
        verbose_name_plural = _('Work location groups')

    def __str__(self):
        return self.name

    class JSONAPIMeta(object):
        resource_name = 'offices/subregions'


class OfficeRestrictionChoices(DjangoChoices):
    office = ChoiceItem(
        'office',
        label=_("Open to people from the same work location")
    )
    office_subregion = ChoiceItem(
        'office_subregion',
        label=_("Open to people from work locations within the same group")
    )
    office_region = ChoiceItem(
        'office_region',
        label=_("Open to people from work locations within the same region")
    )
    all = ChoiceItem(
        'all',
        label=_("Open to people from any work location")
    )
