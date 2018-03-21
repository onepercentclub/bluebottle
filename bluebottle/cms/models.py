from django.db import models
from django.utils.translation import ugettext_lazy as _

from adminsortable.models import SortableMixin
from fluent_contents.models import PlaceholderField, ContentItem
from adminsortable.fields import SortableForeignKey
from parler.models import TranslatableModel, TranslatedFields

from bluebottle.geo.models import Location
from bluebottle.projects.models import Project
from bluebottle.surveys.models import Survey
from bluebottle.tasks.models import Task
from bluebottle.utils.fields import ImageField
from bluebottle.categories.models import Category
from bluebottle.utils.models import BasePlatformSettings
from bluebottle.utils.validators import FileExtensionValidator


class ResultPage(TranslatableModel):
    image = models.ImageField(_('Header image'), blank=True, null=True)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    content = PlaceholderField('content', plugins=[
        'ProjectImagesBlockPlugin',
        'ProjectMapBlockPlugin',
        'ProjectsBlockPlugin',
        'QuotesBlockPlugin',
        'ShareResultsBlockPlugin',
        'StatsBlockPlugin',
        'SurveyBlockPlugin',
        'TasksBlockPlugin',
    ])

    translations = TranslatedFields(
        title=models.CharField(_('Title'), max_length=40),
        slug=models.SlugField(_('Slug'), max_length=40),
        description=models.CharField(_('Description'), max_length=45, blank=True, null=True)
    )

    class Meta:
        permissions = (
            ('api_read_resultpage', 'Can view result pages through the API'),
            ('api_add_resultpage', 'Can add result pages through the API'),
            ('api_change_resultpage', 'Can change result pages through the API'),
            ('api_delete_resultpage', 'Can delete result pages through the API'),
        )


class HomePage(TranslatableModel):
    content = PlaceholderField('content')
    translations = TranslatedFields()

    class Meta:
        permissions = (
            ('api_read_homepage', 'Can view homepages through the API'),
            ('api_add_homepage', 'Can add homepages through the API'),
            ('api_change_homepage', 'Can change homepages through the API'),
            ('api_delete_homepage', 'Can delete homepages through the API'),
        )


class LinkPermission(models.Model):
    permission = models.CharField(max_length=255, null=False,
                                  help_text=_('A dot separated app name and permission codename.'))
    present = models.BooleanField(null=False, default=True,
                                  help_text=_('Should the permission be present or not to access the link?'))

    def __unicode__(self):
        return u"{0} - {1}".format(self.permission, self.present)


class SiteLinks(models.Model):
    language = models.OneToOneField('utils.Language', null=False)
    has_copyright = models.BooleanField(null=False, default=True)

    class Meta:
        verbose_name_plural = _("Site links")

    def __unicode__(self):
        return u"Site Links {0}".format(self.language.code.upper())


class LinkGroup(SortableMixin):
    GROUP_CHOICES = (
        ('main', _('Main')),
        ('about', _('About')),
        ('info', _('Info')),
        ('discover', _('Discover')),
        ('social', _('Social')),
    )

    site_links = models.ForeignKey(SiteLinks, related_name='link_groups')
    name = models.CharField(max_length=25, choices=GROUP_CHOICES, default='main')
    title = models.CharField(_('Title'), blank=True, max_length=50)
    group_order = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    class Meta:
        ordering = ['group_order']


class Link(SortableMixin):
    COMPONENT_CHOICES = (
        ('page', _('Page')),
        ('project', _('Project')),
        ('task', _('Task')),
        ('fundraiser', _('Fundraiser')),
        ('results-page', _('Results Page')),
        ('news', _('News')),
    )

    link_group = SortableForeignKey(LinkGroup, related_name='links')
    link_permissions = models.ManyToManyField(LinkPermission, blank=True)
    highlight = models.BooleanField(default=False)
    title = models.CharField(_('Title'), null=False, max_length=100)
    component = models.CharField(_('Component'), choices=COMPONENT_CHOICES, max_length=50,
                                 blank=True, null=True)
    component_id = models.CharField(_('Component ID'), max_length=100, blank=True, null=True)
    external_link = models.CharField(_('External Link'), max_length=2000, blank=True, null=True)
    link_order = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    class Meta:
        ordering = ['link_order']


class Stat(SortableMixin, models.Model):
    STAT_CHOICES = [
        ('manual', _('Manual input')),
        ('people_involved', _('People involved')),
        ('participants', _('Participants')),
        ('projects_realized', _('Projects realised')),
        ('projects_complete', _('Projects complete')),
        ('tasks_realized', _('Tasks realised')),
        ('task_members', _('Taskmembers')),
        ('donated_total', _('Donated total')),
        ('pledged_total', _('Pledged total')),
        ('amount_matched', _('Amount matched')),
        ('projects_online', _('Projects Online')),
        ('votes_cast', _('Votes casts')),
        ('time_spent', _('Time spent')),
        ('members', _("Number of members"))
    ]

    type = models.CharField(
        max_length=25,
        choices=STAT_CHOICES
    )
    value = models.CharField(max_length=63, null=True, blank=True,
                             help_text=_('Use this for \'manual\' input or the override the calculated value.'))
    block = models.ForeignKey('cms.StatsContent', related_name='stats', null=True)
    sequence = models.PositiveIntegerField(default=0, editable=False, db_index=True)
    title = models.CharField(max_length=63)

    @property
    def name(self):
        return self.title

    class Meta:
        ordering = ['sequence']


class Quote(models.Model):
    block = models.ForeignKey('cms.QuotesContent', related_name='quotes')
    name = models.CharField(max_length=60)
    quote = models.TextField()
    image = ImageField(
        _("Image"), max_length=255, blank=True, null=True,
        upload_to='quote_images/'
    )


class TitledContent(ContentItem):
    title = models.CharField(max_length=50, blank=True, null=True)
    sub_title = models.CharField(max_length=400, blank=True, null=True)

    preview_template = 'admin/cms/preview/default.html'

    class Meta:
        abstract = True


class QuotesContent(TitledContent):
    type = 'quotes'
    preview_template = 'admin/cms/preview/quotes.html'

    class Meta:
        verbose_name = _('Quotes')

    def __unicode__(self):
        return unicode(self.quotes)


class StatsContent(TitledContent):
    type = 'statistics'
    preview_template = 'admin/cms/preview/stats.html'

    class Meta:
        verbose_name = _('Platform Statistics')

    def __unicode__(self):
        return unicode(self.stats)


class SurveyContent(TitledContent):
    type = 'survey'
    preview_template = 'admin/cms/preview/results.html'
    survey = models.ForeignKey(Survey, null=True)

    class Meta:
        verbose_name = _('Platform Results')

    def __unicode__(self):
        return unicode(self.survey)


class ProjectsContent(TitledContent):
    type = 'projects'
    action_text = models.CharField(max_length=80,
                                   default=_('Start your own project'),
                                   blank=True, null=True)
    action_link = models.CharField(max_length=100, default="/start-project",
                                   blank=True, null=True)

    projects = models.ManyToManyField(
        Project, blank=True, db_table='cms_projectscontent_projects'
    )
    from_homepage = models.BooleanField(default=False)

    preview_template = 'admin/cms/preview/projects.html'

    class Meta:
        verbose_name = _('Projects')

    def __unicode__(self):
        return unicode(self.title)


class ProjectImagesContent(TitledContent):
    type = 'project_images'
    preview_template = 'admin/cms/preview/project_images.html'

    description = models.TextField(max_length=70, blank=True, null=True)
    action_text = models.CharField(max_length=40,
                                   default=_('Check out our projects'),
                                   blank=True, null=True)
    action_link = models.CharField(max_length=100, default="/projects?status=campaign%2Cvoting ",
                                   blank=True, null=True)

    class Meta:
        verbose_name = _('Project Images')

    def __unicode__(self):
        return 'Project images block'


class ShareResultsContent(TitledContent):
    type = 'share-results'
    preview_template = 'admin/cms/preview/share_results.html'

    share_title = models.CharField(max_length=100, default='')
    share_text = models.CharField(
        max_length=100,
        default='',
        help_text="{amount}, {projects}, {tasks}, {hours}, {votes}, {people} will be replaced by live statistics"
    )

    class Meta:
        verbose_name = _('Share Results')

    def __unicode__(self):
        return 'Share results block'


class TasksContent(TitledContent):
    type = 'tasks'
    preview_template = 'admin/cms/preview/tasks.html'
    action_text = models.CharField(max_length=40, blank=True, null=True)
    action_link = models.CharField(max_length=100, blank=True, null=True)

    tasks = models.ManyToManyField(Task, db_table='cms_taskscontent_tasks')

    class Meta:
        verbose_name = _('Tasks')

    def __unicode__(self):
        return 'Tasks'


class ProjectsMapContent(TitledContent):
    type = 'projects-map'

    class Meta:
        verbose_name = _('Projects Map')

    def __unicode__(self):
        return 'Projects Map'


class SupporterTotalContent(TitledContent):
    type = 'supporter_total'
    preview_template = 'admin/cms/preview/supporter_total.html'

    co_financer_title = models.CharField(max_length=70, blank=True, null=True)

    class Meta:
        verbose_name = _('Supporter total')

    def __unicode__(self):
        return 'Supporter total'


class Slide(SortableMixin, models.Model):
    block = models.ForeignKey('cms.SlidesContent', related_name='slides')
    tab_text = models.CharField(
        _("Tab text"), max_length=100,
        help_text=_("This is shown on tabs beneath the banner.")
    )
    title = models.CharField(_("Title"), max_length=100, blank=True)
    body = models.TextField(_("Body text"), blank=True)
    image = ImageField(
        _("Image"), max_length=255, blank=True, null=True,
        upload_to='banner_slides/'
    )
    background_image = ImageField(
        _("Background image"), max_length=255, blank=True,
        null=True, upload_to='banner_slides/'
    )
    video_url = models.URLField(
        _("Video url"), max_length=100, blank=True, default=''
    )
    link_text = models.CharField(
        _("Link text"), max_length=400,
        help_text=_("This is the text on the button inside the banner."),
        blank=True
    )
    link_url = models.CharField(
        _("Link url"), max_length=400,
        help_text=_("This is the link for the button inside the banner."),
        blank=True
    )
    sequence = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    class Meta:
        ordering = ['sequence']


class SlidesContent(TitledContent):
    type = 'slides'

    class Meta:
        verbose_name = _('Slides')

    def __unicode__(self):
        return unicode(self.slides)


class Step(SortableMixin, models.Model):
    block = models.ForeignKey('cms.StepsContent', related_name='steps')
    image = ImageField(
        _("Image"), max_length=255, blank=True, null=True,
        upload_to='step_images/'
    )
    header = models.CharField(_("Header"), max_length=100)
    text = models.CharField(_("Text"), max_length=400, null=True, blank=True)
    sequence = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    class Meta:
        ordering = ['sequence']


class StepsContent(TitledContent):
    action_text = models.CharField(max_length=40,
                                   default=_('Start your own project'),
                                   blank=True, null=True)
    action_link = models.CharField(max_length=100, default="/start-project",
                                   blank=True, null=True)

    type = 'steps'

    class Meta:
        verbose_name = _('Steps')

    def __unicode__(self):
        return unicode(_('Steps'))


class LocationsContent(TitledContent):
    type = 'locations'
    locations = models.ManyToManyField(Location, db_table='cms_locationscontent_locations')

    class Meta:
        verbose_name = _('Locations')

    def __unicode__(self):
        return unicode(_('Locations'))


class CategoriesContent(TitledContent):
    type = 'categories'
    categories = models.ManyToManyField(Category, db_table='cms_categoriescontent_categories')

    class Meta:
        verbose_name = _('Categories')

    def __unicode__(self):
        return unicode(_('Categories'))


class Logo(SortableMixin, models.Model):
    block = models.ForeignKey('cms.LogosContent', related_name='logos')
    image = ImageField(
        _("Image"), max_length=255, blank=True, null=True,
        upload_to='logo_images/'
    )
    link = models.CharField(max_length=100, blank=True, null=True)
    sequence = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    class Meta:
        ordering = ['sequence']


class LogosContent(TitledContent):
    type = 'logos'
    action_text = models.CharField(max_length=40, null=True, blank=True)
    action_link = models.CharField(
        max_length=100,
        default="/start-project",
        blank=True, null=True
    )

    class Meta:
        verbose_name = _('Logos')

    def __unicode__(self):
        return unicode(_('Logos'))


class ContentLink(SortableMixin, models.Model):
    block = models.ForeignKey('cms.LinksContent', related_name='links')
    image = ImageField(
        _("Image"), max_length=255, blank=True, null=True,
        upload_to='link_images/'
    )
    action_text = models.CharField(max_length=40)
    action_link = models.CharField(
        max_length=100, blank=True, null=True
    )
    sequence = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    class Meta:
        ordering = ['sequence']


class LinksContent(TitledContent):
    type = 'links'

    class Meta:
        verbose_name = _('Links')

    def __unicode__(self):
        return unicode(_('Links'))


class Greeting(models.Model):
    block = models.ForeignKey('cms.WelcomeContent', related_name='greetings')
    text = models.TextField()


class WelcomeContent(ContentItem):
    type = 'welcome'
    preview_template = 'admin/cms/preview/default.html'

    preamble = models.CharField(max_length=20)

    class Meta:
        verbose_name = _('Welcome')

    def __unicode__(self):
        return unicode(_('Welcome'))


class SitePlatformSettings(BasePlatformSettings):
    logo = models.ImageField(null=True, blank=True, upload_to='site_content/')

    contact_email = models.EmailField(null=True, blank=True)
    contact_phone = models.CharField(max_length=100, null=True, blank=True)
    copyright = models.CharField(max_length=100, null=True, blank=True)
    powered_by_text = models.CharField(max_length=100, null=True, blank=True)
    powered_by_link = models.CharField(max_length=100, null=True, blank=True)
    powered_by_logo = models.ImageField(null=True, blank=True, upload_to='site_content/')
    logo = models.FileField(
        null=True, blank=True, upload_to='site_content/',
        validators=[FileExtensionValidator(allowed_extensions=['svg'])]
    )
    favicon = models.ImageField(null=True, blank=True, upload_to='site_content/')

    class Meta:
        verbose_name_plural = _('site platform settings')
        verbose_name = _('site platform settings')
