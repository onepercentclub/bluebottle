from django.utils.translation import ugettext_lazy as _
from django.db import models

from fluent_contents.models import PlaceholderField, ContentItem
from fluent_contents.extensions import plugin_pool, ContentPlugin

from bluebottle.surveys.models import Survey
from bluebottle.projects.models import Project
from adminsortable.models import SortableMixin
from adminsortable.fields import SortableForeignKey


class ResultPage(models.Model):
    title = models.CharField(_('Title'), max_length=200)
    slug = models.SlugField(_('Slug'), max_length=200)
    description = models.TextField(_('Description'), blank=True, null=True)
    image = models.ImageField(_('Header image'), blank=True, null=True)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    content = PlaceholderField('content')


class Stats(models.Model):
    def __unicode__(self):
        return u"List of statistics #{0}".format(self.id)


class Stat(SortableMixin):
    STAT_CHOICES = [
        ('manual', _('Manual input')),
        ('people_involved', _('People involved')),
        ('projects_realized', _('Projects realised')),
        ('tasks_realized', _('Tasks realised')),
        ('donated_total', _('Donated total')),
        ('projects_online', _('Projects Online')),
        ('votes_cast', _('Votes casts')),
    ]

    type = models.CharField(
        max_length=40,
        choices=STAT_CHOICES
    )
    title = models.CharField(max_length=63)
    value = models.CharField(max_length=63, null=True, blank=True,
                             help_text=_('Use this for \'manual\' input or the override the calculated value.'))
    stats = SortableForeignKey(Stats)
    sequence = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    class Meta:
        ordering = ['sequence']


class Quotes(models.Model):
    def __unicode__(self):
        return u"List of quotes #{0}".format(self.id)


class Quote(models.Model):
    name = models.CharField(max_length=63)
    quote = models.CharField(max_length=255)
    quotes = models.ForeignKey(Quotes)


class QuotesContent(ContentItem):
    type = 'quotes'
    quotes = models.ForeignKey(Quotes)
    preview_template = 'admin/cms/preview/quotes.html'

    title = models.CharField(max_length=63, blank=True, null=True)
    sub_title = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = _('Quotes')

    def __unicode__(self):
        return unicode(self.quotes)


class StatsContent(ContentItem):
    type = 'statistics'
    stats = models.ForeignKey(Stats)
    preview_template = 'admin/cms/preview/stats.html'
    title = models.CharField(max_length=63, blank=True, null=True)
    sub_title = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = _('Platform Statistics')

    def __unicode__(self):
        return unicode(self.stats)


class SurveyContent(ContentItem):
    type = 'survey'
    preview_template = 'admin/cms/preview/results.html'
    survey = models.ForeignKey(Survey, null=True)
    title = models.CharField(max_length=63, blank=True, null=True)
    sub_title = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = _('Platform Results')

    def __unicode__(self):
        return unicode(self.survey)


class Projects(models.Model):
    projects = models.ManyToManyField(Project)

    def __unicode__(self):
        return u"List of projects #{0}".format(self.id)


class ProjectsContent(ContentItem):
    title = models.CharField(max_length=63, blank=True, null=True)
    sub_title = models.CharField(max_length=100, blank=True, null=True)

    action_text = models.CharField(max_length=100,
                                   default=_('Add your own project'),
                                   blank=True, null=True)
    action_link = models.CharField(max_length=100, default="/start-project",
                                   blank=True, null=True)

    projects = models.ForeignKey(Projects, null=True)

    type = 'projects'
    preview_template = 'admin/cms/preview/projects.html'

    class Meta:
        verbose_name = _('Projects')

    def __unicode__(self):
        return unicode(self.projects)


class ProjectImagesContent(ContentItem):
    type = 'project_images'
    preview_template = 'admin/cms/preview/project_images.html'

    title = models.CharField(max_length=63, blank=True, null=True)
    sub_title = models.CharField(max_length=100, blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    action_text = models.CharField(max_length=100,
                                   default=_('Check out our projects'),
                                   blank=True, null=True)
    action_link = models.CharField(max_length=100, default="/projects",
                                   blank=True, null=True)

    class Meta:
        verbose_name = _('Project Images')

    def __unicode__(self):
        return 'Project images block'


class ShareResultsContent(ContentItem):
    type = 'share-results'
    preview_template = 'admin/cms/preview/share_results.html'

    title = models.CharField(max_length=63, blank=True, null=True)
    sub_title = models.CharField(max_length=100, blank=True, null=True)

    share_text = models.CharField(max_length=100)

    class Meta:
        verbose_name = _('Share Results')

    def __unicode__(self):
        return 'Share results block'


class ResultsContentPlugin(ContentPlugin):
    admin_form_template = 'admin/cms/content_item.html'

    category = _('Results')


@plugin_pool.register
class QuotesBlockPlugin(ResultsContentPlugin):
    model = QuotesContent


@plugin_pool.register
class StatsBlockPlugin(ResultsContentPlugin):
    model = StatsContent


@plugin_pool.register
class SurveyBlockPlugin(ResultsContentPlugin):
    model = SurveyContent


@plugin_pool.register
class ProjectsBlockPlugin(ResultsContentPlugin):
    model = ProjectsContent


@plugin_pool.register
class ProjectImagesBlockPlugin(ResultsContentPlugin):
    model = ProjectImagesContent


@plugin_pool.register
class ShareResultsBlockPlugin(ResultsContentPlugin):
    model = ShareResultsContent
