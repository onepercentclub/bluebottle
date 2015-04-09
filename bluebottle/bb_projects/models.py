from bluebottle.bb_projects.fields import MoneyField
from bluebottle.utils.utils import StatusDefinition
from django.db.models.aggregates import Sum
from django.db.models.query_utils import Q
from taggit.managers import TaggableManager
from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from django.db.models import options

from django_extensions.db.fields import (
    ModificationDateTimeField, CreationDateTimeField)
from bluebottle.utils.fields import ImageField

from bluebottle.utils.model_dispatcher import get_project_phaselog_model
from bluebottle.utils.utils import GetTweetMixin

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('default_serializer', 'preview_serializer', 'manage_serializer')


class ProjectTheme(models.Model):
    """ Themes for Projects. """

    # The name is marked as unique so that users can't create duplicate theme names.
    name = models.CharField(_('name'), max_length=100, unique=True)
    name_nl = models.CharField(_('name NL'), max_length=100, unique=True)
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

    slug = models.SlugField(max_length=200, unique=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=400, blank=True)
    sequence = models.IntegerField(unique=True, help_text=_('For ordering phases.'))

    active = models.BooleanField(default=True, help_text=_('Whether this phase is in use or has been discarded.'))
    editable = models.BooleanField(default=True,
                                   help_text=_('Whether the project owner can change the details of the project.'))
    viewable = models.BooleanField(default=True,
                                   help_text=_('Whether this phase, and projects in it show up at the website'))
    owner_editable = models.BooleanField(default=False,
                                   help_text=_('The owner can manually select between these phases'))


    class Meta():
        ordering = ['sequence']

    def __unicode__(self):
        return u'{0} - {1}'.format(self.sequence,  self.name)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(ProjectPhase, self).save(*args, **kwargs)


class BaseProjectManager(models.Manager):

    def search(self, query):
        qs = super(BaseProjectManager, self).get_query_set()

        # Apply filters
        status = query.getlist(u'status[]', None)
        if status:
            qs = qs.filter(status_id__in=status)
        else:
            status = query.get('status', None)
            if status:
                qs = qs.filter(status_id=status)

        country = query.get('country', None)
        if country:
            qs = qs.filter(country=country)

        theme = query.get('theme', None)
        if theme:
            qs = qs.filter(theme_id=theme)

        text = query.get('text', None)
        if text:
            qs = qs.filter(Q(title__icontains=text) |
                           Q(pitch__icontains=text) |
                           Q(description__icontains=text))

        return self._ordering(query.get('ordering', None), qs)

    def _ordering(self, ordering, queryset):

        if ordering == 'deadline':
            qs = queryset.order_by('deadline')
        elif ordering == 'newest':
            qs = queryset.order_by('-created')
        elif ordering:
            qs = queryset.order_by(ordering)
        else:
            qs = queryset

        return qs


class BaseProject(models.Model, GetTweetMixin):
    """ The base Project model. """
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('initiator'),
        help_text=_('Project owner'), related_name='owner')

    organization = models.ForeignKey(
        settings.ORGANIZATIONS_ORGANIZATION_MODEL, verbose_name=_('organization'),
        help_text=_('Project organization'), related_name='organization', null=True, blank=True)

    # Basics
    created = CreationDateTimeField(_('created'), help_text=_('When this project was created.'))
    updated = ModificationDateTimeField(_('updated'))
    title = models.CharField(_('title'), max_length=255, unique=True)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    pitch = models.TextField(_('pitch'), help_text=_('Pitch your smart idea in one sentence'), blank=True)
    status = models.ForeignKey('bb_projects.ProjectPhase')
    theme = models.ForeignKey('bb_projects.ProjectTheme', null=True, blank=True)
    favorite = models.BooleanField(default=True)
    tags = TaggableManager(blank=True, verbose_name=_('tags'), help_text=_('Add tags'))

    deadline = models.DateTimeField(_('deadline'), null=True, blank=True)


    # Extended Description
    description = models.TextField(_('why, what and how'), help_text=_('Blow us away with the details!'), blank=True)

    # Media
    image = ImageField(
        _('image'), max_length=255, blank=True, upload_to='project_images/',
        help_text=_('Main project picture'))

    country = models.ForeignKey('geo.Country', blank=True, null=True)
    language = models.ForeignKey('utils.Language', blank=True, null=True)

    # For convenience and performance we also store money donated and needed here.
    amount_asked = MoneyField(default=0, null=True, blank=True)
    amount_donated = MoneyField(default=0)
    amount_needed = MoneyField(default=0)
    amount_extra = MoneyField(default=0, null=True, blank=True,
                              help_text=_("Amount pledged by organisation (matching fund)."))


    @property
    def is_realised(self):
        return self.status == ProjectPhase.objects.get(slug='done-complete')

    @property
    def amount_pending(self):
        return self.get_amount_total([StatusDefinition.PENDING])

    @property
    def amount_safe(self):
        return self.get_amount_total([StatusDefinition.SUCCESS])

    _initial_status = None

    objects = BaseProjectManager()

    class Meta:
        abstract = True
        ordering = ['title']
        verbose_name = _('project')
        verbose_name_plural = _('projects')
        default_serializer = 'bluebottle.bb_projects.serializers.ProjectSerializer'
        preview_serializer = 'bluebottle.bb_projects.serializers.ProjectPreviewSerializer'
        manage_serializer = 'bluebottle.bb_projects.serializers.ManageProjectSerializer'

    def __unicode__(self):
        return self.slug if not self.title else self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            original_slug = slugify(self.title)
            counter = 2
            qs = self.__class__.objects

            while qs.filter(slug=original_slug).exists():
                original_slug = '{0}-{1}'.format(original_slug, counter)
                counter += 1
            self.slug = original_slug

        previous_status = None
        if self.pk:
            previous_status = self.__class__.objects.get(pk=self.pk).status
        super(BaseProject, self).save(*args, **kwargs)

        # Only log project phase if the status has changed
        if self != None and previous_status != self.status:
            get_project_phaselog_model().objects.create(project=self, status=self.status)

    @models.permalink
    def get_absolute_url(self):
        url = "/#!/projects/{0}".format(self.slug)
        return url

    def update_amounts(self, save=True):
        """
        Update amount_donated and amount_needed
        """
        self.amount_donated = self.get_amount_total([StatusDefinition.SUCCESS, StatusDefinition.PENDING])
        self.amount_needed = self.amount_asked - self.amount_donated

        if self.amount_needed < 0:
            # Should never be less than zero
            self.amount_needed = 0

        if save:
            self.save()

    def get_amount_total(self, status_in=None):
        """
        Calculate the total (real time) amount of money for donations, filtered by status.
        """

        if self.amount_asked == 0:
            # No money asked, return 0
            return 0

        donations = self.donation_set.all()

        if status_in:
            donations = donations.filter(order__status__in=status_in)

        total = donations.aggregate(sum=Sum('amount'))

        if not total['sum']:
            # No donations, manually set amount to 0
            return 0

        return total['sum']

    @property
    def editable(self):
        return self.status.editable

    @property
    def viewable(self):
        return self.status.viewable

    def set_status(self, phase_slug, save=True):
        self.status = ProjectPhase.objects.get(slug=phase_slug)
        if save:
            self.save()


class BaseProjectPhaseLog(models.Model):
    project = models.ForeignKey(settings.PROJECTS_PROJECT_MODEL)
    status = models.ForeignKey("bb_projects.ProjectPhase")
    start = CreationDateTimeField(_('created'), help_text=_('When this project entered in this status.'))

    class Meta():
        abstract = True


from projectwallmails import *
