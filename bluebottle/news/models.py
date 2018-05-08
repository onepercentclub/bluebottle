from django.conf import settings
from django.db import models
from django.template.defaultfilters import truncatechars
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils.functional import lazy

from django_extensions.db.fields import (CreationDateTimeField,
                                         ModificationDateTimeField)
from djchoices import DjangoChoices, ChoiceItem
from fluent_contents.models import PlaceholderField, ContentItemRelation
from fluent_contents.rendering import render_placeholder

from bluebottle.utils.fields import ImageField
from bluebottle.utils.serializers import MLStripper
from bluebottle.clients import properties

from .managers import NewsItemManager


def get_languages():
    return properties.LANGUAGES


class NewsItem(models.Model):
    class PostStatus(DjangoChoices):
        published = ChoiceItem('published', label=_("Published"))
        draft = ChoiceItem('draft', label=_("Draft"))

    title = models.CharField(_("Title"), max_length=200)
    slug = models.SlugField(_("Slug"))

    # Contents
    main_image = ImageField(_("Main image"),
                            help_text=_("Shows at the top of your post."),
                            upload_to='blogs', blank=True)
    language = models.CharField(_("language"),
                                max_length=5,
                                choices=lazy(get_languages, tuple)())
    contents = PlaceholderField("blog_contents", plugins=[
        'TextPlugin',
        'ImageTextPlugin',
        'RawHtmlPlugin',
        'PicturePlugin'
    ])
    # This should not be nessecary, but fixes deletion of some news items
    # See https://github.com/edoburu/django-fluent-contents/issues/19
    contentitem_set = ContentItemRelation()

    # Publication
    status = models.CharField(_('status'), max_length=20,
                              choices=PostStatus.choices,
                              default=PostStatus.draft, db_index=True)
    publication_date = models.DateTimeField(
        _('publication date'), null=True, db_index=True,
        help_text=_("To go live, status must be 'Published'."))

    publication_end_date = models.DateTimeField(_('publication end date'),
                                                null=True, blank=True,
                                                db_index=True)
    allow_comments = models.BooleanField(_("Allow comments"), default=True)

    # Metadata
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name=_('author'), blank=True, null=True)
    creation_date = CreationDateTimeField(_('creation date'))
    modification_date = ModificationDateTimeField(_('last modification'))

    objects = NewsItemManager()

    def __unicode__(self):
        return self.title

    def get_meta_description(self, **kwargs):
        request = kwargs.get('request')
        s = MLStripper()
        s.feed(mark_safe(render_placeholder(request, self.contents).html))
        return truncatechars(s.get_data(), 250)

    class Meta:
        verbose_name = _("news item")
        verbose_name_plural = _("news items")
