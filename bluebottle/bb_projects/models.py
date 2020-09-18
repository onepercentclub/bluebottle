from builtins import object
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatedFields

from bluebottle.utils.models import SortableTranslatableModel


class ProjectTheme(SortableTranslatableModel):

    """ Themes for Projects. """

    # The name is marked as unique so that users can't create duplicate
    # theme names.
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    disabled = models.BooleanField(_('disabled'), default=False)

    translations = TranslatedFields(
        name=models.CharField(_('name'), max_length=100),
        description=models.TextField(_('description'), blank=True)
    )

    def __unicode__(self):
        return self.name

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super(ProjectTheme, self).save(**kwargs)

    class Meta(object):
        ordering = ['translations__name']
        verbose_name = _('project theme')
        verbose_name_plural = _('project themes')
        permissions = (
            ('api_read_projecttheme', 'Can view project theme through API'),
        )
