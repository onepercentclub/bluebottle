from django.conf import settings
from django.db import models
from django.template.defaultfilters import truncatechars
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from django_extensions.db.fields import (
    CreationDateTimeField, ModificationDateTimeField)
from djchoices import DjangoChoices, ChoiceItem
from fluent_contents.models import PlaceholderField
from fluent_contents.rendering import render_placeholder

from bluebottle.utils.serializers import MLStripper

GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_page', 'change_page', 'delete_page',
        )
    }
}


class Page(models.Model):
    """
    Slides for homepage.
    """

    class PageStatus(DjangoChoices):
        published = ChoiceItem('published', label=_('Published'))
        draft = ChoiceItem('draft', label=_('Draft'))

    title = models.CharField(_('Title'), max_length=200)
    slug = models.SlugField(_('Slug'), unique=False)
    full_page = models.BooleanField(default=False, help_text=_(
        'Show this page in full page width.'))

    # Contents
    language = models.CharField(
        _('language'), max_length=5, choices=settings.LANGUAGES)
    body = PlaceholderField('blog_contents')

    # Publication
    status = models.CharField(
        _('status'), max_length=20, choices=PageStatus.choices,
        default=PageStatus.draft, db_index=True)
    publication_date = models.DateTimeField(
        _('publication date'), null=True, db_index=True,
        help_text=_("When the entry goes live, status must be 'Published'"))
    publication_end_date = models.DateTimeField(
        _('publication end date'), null=True, blank=True, db_index=True)

    # Metadata
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('author'), editable=False,
        null=True)
    creation_date = CreationDateTimeField(_('creation date'))
    modification_date = ModificationDateTimeField(_('last modification'))

    class Meta:
        ordering = ('language', 'slug')
        unique_together = ('language', 'slug')

    def __unicode__(self):
        return self.title

    def get_meta_description(self, **kwargs):
        request = kwargs.get('request')
        s = MLStripper()
        s.feed(mark_safe(render_placeholder(request, self.body).html))
        return truncatechars(s.get_data(), 200)
