from django.conf import settings
from django.db import models
from django.utils.functional import lazy
from django.utils.translation import gettext_lazy as _
from djchoices import DjangoChoices, ChoiceItem
from future.utils import python_2_unicode_compatible

from bluebottle.utils.models import PublishableModel, get_language_choices


@python_2_unicode_compatible
class Quote(PublishableModel):
    """
    Slides for homepage
    """

    class QuoteStatus(DjangoChoices):
        published = ChoiceItem('published', label=_("Published"))
        draft = ChoiceItem('draft', label=_("Draft"))

    # Contents
    language = models.CharField(_("language"), max_length=7,
                                choices=lazy(get_language_choices, list)())
    quote = models.TextField()
    role = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             verbose_name=_('Quoted member'),
                             related_name="quote_user",
                             on_delete=models.CASCADE)

    def __str__(self):
        return self.quote

    class Meta:
        ordering = ('-publication_date',)
