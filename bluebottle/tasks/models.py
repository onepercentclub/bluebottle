from builtins import object
from django.db import models
from django.utils.translation import ugettext_lazy as _
from future.utils import python_2_unicode_compatible
from parler.models import TranslatedFields

from bluebottle.utils.models import SortableTranslatableModel


@python_2_unicode_compatible
class Skill(SortableTranslatableModel):
    expertise = models.BooleanField(_('expertise based'),
                                    help_text=_('Is this skill expertise based, or could anyone do it?'),
                                    default=True)
    disabled = models.BooleanField(_('disabled'), default=False)

    translations = TranslatedFields(
        name=models.CharField(_('name'), max_length=100, ),
        description=models.TextField(_('description'), blank=True)
    )

    def __str__(self):
        return self.name

    class Meta(object):
        permissions = (
            ('api_read_skill', 'Can view skills through the API'),
        )
        verbose_name = _(u'Skill')
        verbose_name_plural = _(u'Skills')
