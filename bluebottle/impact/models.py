from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatedFields

from bluebottle.utils.models import SortableTranslatableModel


class ImpactType(SortableTranslatableModel):

    """ Themes for Projects. """

    # The name is marked as unique so that users can't create duplicate
    # theme names.
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    active = models.BooleanField(_('active'), default=True)

    translations = TranslatedFields(
        name=models.CharField(_('name'), max_length=100),
        unit=models.CharField(_('unit'), blank=True, max_length=100)
    )

    def __unicode__(self):
        return self.name

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super(ImpactType, self).save(**kwargs)

    class Meta:
        ordering = ['translations__name']
        verbose_name = _('impact type')
        verbose_name_plural = _('impact types')


class ImpactGoal(models.Model):
    type = models.ForeignKey(
        ImpactType,
        verbose_name=_('type'),
    )
    activity = models.ForeignKey(
        'activities.activity',
        verbose_name=_('activity'),
        related_name='goals'
    )

    target = models.FloatField(_('target'), blank=False, null=True)
    realized = models.FloatField(_('realized'), blank=False, null=True)
