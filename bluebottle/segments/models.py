from django.contrib.postgres.fields import ArrayField
from django.template.defaultfilters import slugify
from django.db import models

from django.utils.translation import ugettext_lazy as _


class SegmentType(models.Model):
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)

    is_active = models.BooleanField(
        _('Is active'),
        default=True
    )
    enable_search = models.BooleanField(
        _('Enable search filters.'),
        default=False
    )

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super(SegmentType, self).save(**kwargs)

    def __unicode__(self):
        return str(self.name)


class Segment(models.Model):
    name = models.CharField(_('name'), max_length=255)

    alternate_names = ArrayField(
        models.CharField(max_length=200),
        blank=True
    )
    type = models.ForeignKey(
        SegmentType,
        verbose_name=_('type'),
        related_name='segments'
    )

    def save(self, *args, **kwargs):
        if self.name not in self.alternate_names:
            self.alternate_names.append(self.name)

        super(Segment, self).save(*args, **kwargs)

    def __unicode__(self):
        return '{}: {}'.format(self.type.name, self.name)
