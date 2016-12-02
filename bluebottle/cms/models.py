from django.utils.translation import ugettext_lazy as _
from django.db import models

from fluent_contents.models import PlaceholderField, ContentItem
from fluent_contents.extensions import plugin_pool, ContentPlugin

from bluebottle.surveys.models import Survey


class ResultPage(models.Model):
    title = models.CharField(_('Title'), max_length=200)
    slug = models.SlugField(_('Slug'), max_length=200)
    description = models.TextField(_('Description'), blank=True, null=True)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    content = PlaceholderField('content')


class Stats(models.Model):
    name = models.CharField(max_length=63)

    def __unicode__(self):
        return self.name


class Stat(models.Model):
    STAT_CHOICES = [
        ('manual', _('Manual input')),
        ('people_involved', _('People involved')),
        ('projects_realized', _('Projects realised')),
        ('tasks_realized', _('Tasks realised')),
        ('donated_total', _('Donated total')),
        ('votes_cast', _('Votes casts')),
    ]

    type = models.CharField(
        max_length=40,
        choices=STAT_CHOICES
    )
    name = models.CharField(max_length=63)
    value = models.CharField(max_length=63, null=True, blank=True,
                             help_text=_('Use this for \'manual\' input or the override the calculated value.'))
    stats = models.ForeignKey(Stats)


class Quotes(models.Model):
    name = models.CharField(max_length=63)

    def __unicode__(self):
        return self.name


class Quote(models.Model):
    name = models.CharField(max_length=63)
    quote = models.CharField(max_length=255)
    quotes = models.ForeignKey(Quotes)


class QuotesContent(ContentItem):
    type = 'quotes'
    quotes = models.ForeignKey(Quotes)
    preview_template = 'admin/cms/preview/quotes.html'

    class Meta:
        verbose_name = _('Quotes')

    def __unicode__(self):
        return _('Quotes')


class StatsContent(ContentItem):
    type = 'statistics'
    stats = models.ForeignKey(Stats)
    preview_template = 'admin/cms/preview/stats.html'

    class Meta:
        verbose_name = _('Platform Statistics')

    def __unicode__(self):
        return _('Platform Statistics')


class ResultsContent(ContentItem):
    type = 'survey'
    preview_template = 'admin/cms/preview/results.html'
    survey = models.ForeignKey(Survey, null=True)

    class Meta:
        verbose_name = _('Platform Results')

    def __unicode__(self):
        return _('Result')


@plugin_pool.register
class QuotesBlockPlugin(ContentPlugin):
    model = QuotesContent
    admin_form_template = 'admin/cms/content_item.html'

    category = _('Results')


@plugin_pool.register
class StatsBlockPlugin(ContentPlugin):
    model = StatsContent
    admin_form_template = 'admin/cms/content_item.html'

    category = _('Results')


@plugin_pool.register
class ResultsBlockPlugin(ContentPlugin):
    model = ResultsContent
    admin_form_template = 'admin/cms/content_item.html'

    category = _('Results')
