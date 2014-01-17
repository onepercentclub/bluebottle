from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import slugify
from django.utils import translation
from django.utils.http import urlquote
from django.utils.translation import ugettext as _

from babel.numbers import format_currency
from django_extensions.db.fields import (
    ModificationDateTimeField, CreationDateTimeField)
from djchoices import DjangoChoices, ChoiceItem
from sorl.thumbnail import ImageField
from taggit_autocomplete_modified.managers import (
    TaggableManagerAutocomplete as TaggableManager)


class ProjectTheme(models.Model):
    """ Themes for Projects. """

    # The name is marked as unique so that users can't create duplicate theme names.
    name = models.CharField(_('name'), max_length=100, unique=True)
    name_nl = models.CharField(_('name'), max_length=100, unique=True)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('project theme')
        verbose_name_plural = _('project themes')

    def __unicode__(self):
        return self.name

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super(ProjectTheme, self).save(**kwargs)


class ProjectPhase(models.Model):
    """ Phase of a project """

    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=400, blank=True)
    sequence = models.IntegerField(unique=True, help_text=_('For ordering phases.'))

    active = models.BooleanField(default=True, help_text=_('Whether this phase is in use or has been discarded.'))

    editable = models.BooleanField(default=True,
                                   help_text=_('Whether the project owner can change the details of the project.'))

    viewable = models.BooleanField(default=True,
                                   help_text=_('Whether this phase, and projects in it show up at the website'))

    class Meta():
        ordering = ['sequence']

    def __unicode__(self):
        return '{0} - {1}'.format(self.sequence,  self.name)


class ProjectManager(models.Manager):
    def order_by(self, field):

        if field == 'deadline':
            qs = self.get_query_set()
            qs = qs.order_by('projectcampaign__deadline')
            return qs

        if field == 'newest':
            qs = self.get_query_set()
            qs = qs.order_by('projectcampaign__money_needed')
            return qs

        qs = super(ProjectManager, self).order_by(field)
        return qs


class BaseProject(models.Model):
    """ The base Project model. """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('initiator'),
        help_text=_('Project owner'), related_name='owner')

    # Basics
    created = CreationDateTimeField(
        _('created'), help_text=_('When this project was created.'))
    updated = ModificationDateTimeField(_('updated'))
    title = models.CharField(_('title'), max_length=255, unique=True)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    pitch = models.TextField(
        _('pitch'), blank=True, help_text=_('Pitch your smart idea in one sentence'))
    status = models.ForeignKey(ProjectPhase)
    theme = models.ForeignKey(ProjectTheme)

    # Extended Description
    description = models.TextField(
        _('why, what and how'), help_text=_('Blow us away with the details!'),
        blank=True)

    # Media
    image = ImageField(
        _('image'), max_length=255, blank=True, upload_to='project_images/',
        help_text=_('Main project picture'))

    organization = models.ForeignKey('organizations.Organization', null=True, blank=True)
    country = models.ForeignKey('geo.Country', blank=True, null=True)

    objects = ProjectManager()

    class Meta:
        abstract = True
        ordering = ['title']
        verbose_name = _('project')
        verbose_name_plural = _('projects')

    def __unicode__(self):
        return self.slug if not self.title else self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            original_slug = slugify(self.title)
            counter = 2
            qs = Project.objects
            while qs.filter(slug=original_slug).exists():
                original_slug = '{0}-{1}'.format(original_slug, counter)
                counter += 1
            self.slug = original_slug

        super(BaseProject, self).save(*args, **kwargs)

    def get_absolute_url(self):
        """ Get the URL for the current project. """
        return reverse('project_detail', kwargs={'slug': self.slug})

    def get_absolute_frontend_url(self):
        """ Insert the hashbang, after the language string """
        url = self.get_absolute_url()
        bits = url.split('/')
        url = '/'.join(bits[:2] + ['#!'] + bits[2:])
        return url

    # TODO: move to mixin
    def get_meta_title(self, **kwargs):
        return u'{name_project} | {country}'.format(
            name_project=self.title,
            country=self.country.name if self.country else '')

    def get_fb_title(self, **kwargs):
        title = _(u'{name_project} in {country}').format(
            name_project=self.title,
            country=self.country.name if self.country else '')

        return title

    def get_tweet(self, **kwargs):
        """ Build the tweet text for the meta data """
        request = kwargs.get('request')
        if request:
            lang_code = request.LANGUAGE_CODE
        else:
            lang_code = 'en'
        twitter_handle = settings.TWITTER_HANDLES.get(
            lang_code, settings.DEFAULT_TWITTER_HANDLE)

        title = urlquote(self.get_fb_title())

        # {URL} is replaced in Ember to fill in the page url, avoiding the
        # need to provide front-end urls in our Django code.
        tweet = _(u'{title} {{URL}} via @{twitter_handle}').format(
            title=title, twitter_handle=twitter_handle)

        return tweet

    @property
    def editable(self):
        return self.status.editable

    @property
    def viewable(self):
        return self.status.viewable


class Project(BaseProject):
    """
    Standard Project model. If there are any extra fields required, provide
    your own Project model by extending ``BaseProject``.
    """
    tags = TaggableManager(
        blank=True, verbose_name=_('tags'), help_text=_('Add tags'))

    # Location
    latitude = models.DecimalField(
        _('latitude'), max_digits=21, decimal_places=18, null=True, blank=True)
    longitude = models.DecimalField(
        _('longitude'), max_digits=21, decimal_places=18, null=True, blank=True)


    reach = models.PositiveIntegerField(
        _('Reach'), help_text=_('How many people do you expect to reach?'),
        blank=True, null=True)

    video_url = models.URLField(
        _('video'), max_length=100, blank=True, null=True, default='',
        help_text=_('Do you have a video pitch or a short movie that '
                    "explains your project? Cool! We can't wait to see it! "
                    "You can paste the link to YouTube or Vimeo video here"))

    class Meta:
        swappable = 'PROJECTS_PROJECT_MODEL'


class ProjectDetailField(models.Model):
    class Types(DjangoChoices):
        text = ChoiceItem('text', label=_('Text field (one line)'))
        textarea = ChoiceItem('textarea', label=_('Text area (multiple lines)'))
        checkbox = ChoiceItem('checkbox', label=_('Checkbox'))
        radio = ChoiceItem('radio', label=_('Radio buttons'))
        select = ChoiceItem('select', label=_('Select menu'))

    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=30, unique=True)
    active = models.BooleanField(default=True)
    description = models.CharField(max_length=300, blank=True)
    type = models.CharField(max_length=100, choices=Types.choices)

    def __unicode__(self):
        return self.name


class ProjectDetailFieldValue(models.Model):
    field = models.ForeignKey('ProjectDetailField')
    value = models.CharField(max_length=200)
    text = models.CharField(max_length=200, blank=True)


class ProjectDetailFieldAttribute(models.Model):
    field = models.ForeignKey('ProjectDetailField')
    attribute = models.CharField(max_length=200)
    value = models.CharField(max_length=200)


class ProjectDetail(models.Model):
    project = models.ForeignKey(settings.PROJECTS_PROJECT_MODEL)
    field = models.ForeignKey(ProjectDetailField)
    value = models.TextField()

    class Meta:
        unique_together = ('project', 'field')


class ProjectBudgetLine(models.Model):
    """
    BudgetLine: Entries to the Project Budget sheet.
    This is the budget for the amount asked from this
    website.
    """
    project = models.ForeignKey(settings.PROJECTS_PROJECT_MODEL)
    description = models.CharField(_('description'), max_length=255, default='')
    currency = models.CharField(max_length=3, default='EUR')
    amount = models.PositiveIntegerField(_('amount (in cents)'))

    created = CreationDateTimeField()
    updated = ModificationDateTimeField()

    class Meta:
        verbose_name = _('budget line')
        verbose_name_plural = _('budget lines')

    def __unicode__(self):
        language = translation.get_language().split('-')[0]
        if not language:
            language = 'en'
        return u'{0} - {1}'.format(
            self.description,
            format_currency(self.amount / 100.0, self.currency, locale=language))
