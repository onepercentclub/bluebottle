from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from djchoices.choices import DjangoChoices, ChoiceItem

from bluebottle.clients import properties
from bluebottle.utils.fields import ImageField
from adminsortable.admin import SortableMixin


class LookerEmbed(models.Model):
    class EmbedTypes(DjangoChoices):
        dashboard = ChoiceItem('dashboard', label=_('Dashboard'))
        look = ChoiceItem('look', label=_('Look'))
        space = ChoiceItem('space', label=_('Space'))

    title = models.CharField(_("name"), max_length=255, unique=True)
    type = models.CharField(_("type"), choices=EmbedTypes.choices, max_length=10)
    looker_id = models.IntegerField(_("Looker Id"))


