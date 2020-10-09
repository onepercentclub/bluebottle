from django.conf import settings
from django.db import models
from django.utils.functional import lazy
from django.utils.translation import ugettext_lazy as _
from djchoices import DjangoChoices, ChoiceItem
from future.utils import python_2_unicode_compatible

from bluebottle.clients import properties
from bluebottle.utils.models import PublishableModel


def get_languages():
    return properties.LANGUAGES


@python_2_unicode_compatible
class Quote(PublishableModel):
    """
    Slides for homepage
    """

    class QuoteStatus(DjangoChoices):
        published = ChoiceItem('published', label=_("Published"))
        draft = ChoiceItem('draft', label=_("Draft"))

    # Contents
    language = models.CharField(_("language"), max_length=5,
                                choices=lazy(get_languages, tuple)())
    quote = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             verbose_name=_('Quoted member'),
                             related_name="quote_user")

    def __str__(self):
        return self.quote

    class Meta:
        ordering = ('-publication_date',)
