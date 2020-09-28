from builtins import object
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from future.utils import python_2_unicode_compatible
from parler.models import TranslatedFields

from bluebottle.utils.models import SortableTranslatableModel


@python_2_unicode_compatible
class ProjectTheme(SortableTranslatableModel):
    """ Themes for initiatives. """
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    disabled = models.BooleanField(_('disabled'), default=False)

    translations = TranslatedFields(
        name=models.CharField(_('name'), max_length=100),
        description=models.TextField(_('description'), blank=True)
    )

    def __str__(self):
        return self.name

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super(ProjectTheme, self).save(**kwargs)

    class Meta(object):
        verbose_name = _('theme')
        verbose_name_plural = _('themes')
        permissions = (
            ('api_read_projecttheme', 'Can view theme through API'),
        )
