from django.utils.translation import ugettext_lazy as _
from django.db import models

from fluent_contents.models import PlaceholderField, ContentItem
from fluent_contents.extensions import plugin_pool, ContentPlugin


class Stats(models.Model):
    name = models.CharField(max_length=63)

    def __unicode__(self):
        return self.name


class Stat(models.Model):
    type = models.CharField(
        max_length=40,
        choices=(('People Involved', 'people_involved'), ('Projects Online', 'projects_online'))
    )
    name = models.CharField(max_length=63)
    stats = models.ForeignKey(Stats)


class Quotes(models.Model):
    name = models.CharField(max_length=63)

    def __unicode__(self):
        return self.name


class Quote(models.Model):
    name = models.CharField(max_length=63)
    quote = models.CharField(max_length=255)
    quotes = models.ForeignKey(Quotes)


class ResultPage(models.Model):
    title = models.CharField('Title', max_length=200)
    start = models.DateField(null=True, blank=True)
    end = models.DateField(null=True, blank=True)
    content = PlaceholderField('content')


class StatsContent(ContentItem):
    title = models.CharField(max_length=63)
    stats = models.ForeignKey(Stats)

    preview_template = 'admin/cms/preview/stats.html'

    class Meta:
        verbose_name = 'Platform Statistics'

    def __unicode__(self):
        return 'Platform Statistics'


class QuotesContent(ContentItem):
    quotes = models.ForeignKey(Quotes)
    preview_template = 'admin/cms/preview/quotes.html'

    class Meta:
        verbose_name = 'Quotes'

    def __unicode__(self):
        return 'Quotes'

class ResultsContent(ContentItem):
    preview_template = 'admin/cms/preview/results.html'

    class Meta:
        verbose_name = 'Platform Results'

    def __unicode__(self):
        return 'Result'



@plugin_pool.register
class QuotesBlockPlugin(ContentPlugin):
    model = QuotesContent
    admin_form_template = 'admin/cms/content_item.html'

    category = _("Results")


@plugin_pool.register
class StatsBlockPlugin(ContentPlugin):
    model = StatsContent
    admin_form_template = 'admin/cms/content_item.html'

    category = _("Results")


@plugin_pool.register
class ResultsBlockPlugin(ContentPlugin):
    model = ResultsContent
    admin_form_template = 'admin/cms/content_item.html'

    category = _("Results")
