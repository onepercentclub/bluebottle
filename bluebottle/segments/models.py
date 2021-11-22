from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _
from django_better_admin_arrayfield.models.fields import ArrayField
from future.utils import python_2_unicode_compatible


@python_2_unicode_compatible
class SegmentType(models.Model):
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)

    is_active = models.BooleanField(
        _('Is active'),
        default=True
    )
    user_editable = models.BooleanField(
        _('Editable in user profile'),
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

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)

    class JSONAPIMeta(object):
        resource_name = 'segment-types'


@python_2_unicode_compatible
class Segment(models.Model):
    name = models.CharField(_('name'), max_length=255)
    slug = models.CharField(_('slug'), max_length=255)

    alternate_names = ArrayField(
        models.CharField(max_length=200),
        default=list,
        blank=True
    )
    type = models.ForeignKey(
        SegmentType,
        verbose_name=_('type'),
        related_name='segments',
        on_delete=models.CASCADE
    )

    def save(self, *args, **kwargs):
        if self.name not in self.alternate_names:
            self.alternate_names.append(self.name)

        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return u'{}: {}'.format(self.type.name, self.name)

    class Meta:
        ordering = ('name',)
        unique_together = (('slug', 'type'), )

    class JSONAPIMeta(object):
        resource_name = 'segments'
