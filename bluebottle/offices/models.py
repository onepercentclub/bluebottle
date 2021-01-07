from builtins import object

from django.db import models
from django.utils.translation import ugettext_lazy as _


class OfficeRegion(models.Model):
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)

    class Meta(object):
        ordering = ['name']
        verbose_name = _('office region')
        verbose_name_plural = _('office regions')

    def __str__(self):
        return self.name


class OfficeSubRegion(models.Model):
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    region = models.ForeignKey(
        'offices.OfficeRegion',
        verbose_name=_('region'),
        null=True, blank=True)

    class Meta(object):
        ordering = ['name']
        verbose_name = _('office group')
        verbose_name_plural = _('office groups')

    def __str__(self):
        return self.name
