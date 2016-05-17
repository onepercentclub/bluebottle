from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Count, Sum, options
from django.template.defaultfilters import slugify
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.utils.timezone import now

from django_extensions.db.fields import (ModificationDateTimeField,
                                         CreationDateTimeField)
from localflavor.generic.models import BICField
from djchoices.choices import DjangoChoices, ChoiceItem
from sorl.thumbnail import ImageField
from taggit.managers import TaggableManager

from bluebottle.bb_projects.fields import MoneyField
from bluebottle.tasks.models import TaskMember
from bluebottle.utils.utils import StatusDefinition, GetTweetMixin


class ProjectTheme(models.Model):

    """ Themes for Projects. """

    # The name is marked as unique so that users can't create duplicate
    # theme names.
    name = models.CharField(_('name'), max_length=100, unique=True)
    name_nl = models.CharField(_('name NL'), max_length=100, unique=True)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    disabled = models.BooleanField(_('disabled'), default=False)

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
    sequence = models.IntegerField(unique=True,
                                   help_text=_('For ordering phases.'))

    active = models.BooleanField(default=True,
                                 help_text=_('Whether this phase is in use or '
                                             'has been discarded.'))
    editable = models.BooleanField(default=True,
                                   help_text=_('Whether the project owner can '
                                               'change the details of the'
                                               'project.'))
    viewable = models.BooleanField(default=True,
                                   help_text=_('Whether this phase, and '
                                               'projects in it show up at the '
                                               'website'))
    owner_editable = models.BooleanField(default=False,
                                         help_text=_('The owner can manually '
                                                     'select between these '
                                                     'phases'))

    class Meta():
        ordering = ['sequence']

    def __unicode__(self):
        return u'{0} - {1}'.format(self.sequence, self.name)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(ProjectPhase, self).save(*args, **kwargs)


class BaseProjectDocument(models.Model):

    """ Document for an Project """

    file = models.FileField(
        upload_to='projects/documents')
    author = models.ForeignKey('members.Member',
                               verbose_name=_('author'), blank=True, null=True)
    project = models.ForeignKey('projects.Project',
                                related_name="documents")
    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('updated'))

    deleted = models.DateTimeField(_('deleted'), null=True, blank=True)

    class Meta:
        verbose_name = _('project document')
        verbose_name_plural = _('project documents')
        abstract = True


class BaseProject(models.Model, GetTweetMixin):

    class Type(DjangoChoices):
        sourcing = ChoiceItem('sourcing', label=_('Crowd-sourcing'))
        funding = ChoiceItem('funding', label=_('Crowd-funding'))
        both = ChoiceItem('both', label=_('Crowd-funding & Crowd-sourcing'))

    """ The base Project model. """
    owner = models.ForeignKey(
        'members.Member', verbose_name=_('initiator'),
        help_text=_('Project owner'), related_name='owner')

    organization = models.ForeignKey(
        'organizations.Organization', verbose_name=_(
            'organization'),
        help_text=_('Project organization'),
        related_name='organization', null=True, blank=True)

    project_type = models.CharField(_('Project type'), max_length=50,
                                    choices=Type.choices, null=True, blank=True)

    # Basics
    created = CreationDateTimeField(
        _('created'), help_text=_('When this project was created.'))
    updated = ModificationDateTimeField(_('updated'))
    title = models.CharField(_('title'), max_length=255, unique=True)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    pitch = models.TextField(
        _('pitch'), help_text=_('Pitch your smart idea in one sentence'),
        blank=True)
    status = models.ForeignKey('bb_projects.ProjectPhase')
    theme = models.ForeignKey(
        'bb_projects.ProjectTheme', null=True, blank=True)
    favorite = models.BooleanField(default=True)
    tags = TaggableManager(
        blank=True, verbose_name=_('tags'), help_text=_('Add tags'))

    deadline = models.DateTimeField(_('deadline'), null=True, blank=True)

    location = models.ForeignKey('geo.Location', null=True, blank=True)
    place = models.CharField(help_text=_('Geographical location'),
                             max_length=100, null=True, blank=True)

    # Extended Description
    description = models.TextField(_('why, what and how'), help_text=_(
        'Blow us away with the details!'), blank=True)

    # Media
    image = ImageField(
        _('image'), max_length=255, blank=True, upload_to='project_images/',
        help_text=_('Main project picture'))

    country = models.ForeignKey('geo.Country', blank=True, null=True)
    language = models.ForeignKey('utils.Language', blank=True, null=True)

    # For convenience and performance we also store money donated and needed
    # here.
    amount_asked = MoneyField(default=0, null=True, blank=True)
    amount_donated = MoneyField(default=0)
    amount_needed = MoneyField(default=0)
    amount_extra = MoneyField(default=0, null=True, blank=True,
                              help_text=_("Amount pledged by organisation (matching fund)."))

    # Bank detail data

    # Account holder Info
    account_holder_name = models.CharField(
        _("account holder name"), max_length=255, null=True, blank=True)
    account_holder_address = models.CharField(
        _("account holder address"), max_length=255, null=True, blank=True)
    account_holder_postal_code = models.CharField(
        _("account holder postal code"), max_length=20, null=True, blank=True)
    account_holder_city = models.CharField(
        _("account holder city"), max_length=255, null=True, blank=True)
    account_holder_country = models.ForeignKey(
        'geo.Country', blank=True, null=True,
        related_name="project_account_holder_country")

    # Bank details
    account_number = models.CharField(_("Account number"), max_length=255,
                                      null=True, blank=True)
    account_bic = BICField(_("account SWIFT-BIC"), null=True, blank=True)
    account_bank_country = models.ForeignKey(
        'geo.Country', blank=True, null=True,
        related_name="project_account_bank_country")

    @property
    def is_realised(self):
        return self.status == ProjectPhase.objects.get(slug='done-complete')

    @property
    def is_closed(self):
        return self.status == ProjectPhase.objects.get(slug='closed')

    @property
    def amount_pending(self):
        return self.get_amount_total([StatusDefinition.PENDING])

    @property
    def amount_safe(self):
        return self.get_amount_total([StatusDefinition.SUCCESS])

    @property
    def people_registered(self):
        counts = self.task_set.filter(
            status='open',
            deadline__gt=now(),
            members__status__in=['accepted', 'realized']
        ).aggregate(total=Count('members'), externals=Sum('members__externals'))

        # If there are no members, externals is None
        return counts['total'] + (counts['externals'] or 0)

    @property
    def people_requested(self):
        return self.task_set.filter(
            status='open',
            deadline__gt=now(),
        ).aggregate(total=Sum('people_needed'))['total']

    _initial_status = None

    class Meta:
        abstract = True
        ordering = ['title']
        verbose_name = _('project')
        verbose_name_plural = _('projects')

    def __unicode__(self):
        return self.slug if not self.title else self.title

    def update_amounts(self, save=True):
        """
        Update amount_donated and amount_needed
        """
        self.amount_donated = self.get_amount_total(
            [StatusDefinition.SUCCESS, StatusDefinition.PENDING,
             StatusDefinition.PLEDGED])
        self.amount_needed = self.amount_asked - self.amount_donated

        if self.amount_needed < 0:
            # Should never be less than zero
            self.amount_needed = 0

        if save:
            self.save()

    def get_amount_total(self, status_in=None):
        """
        Calculate the total (real time) amount of money for donations,
        filtered by status.
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

    @cached_property
    def funding(self):
        """
        Return the amount of people funding this project
        """
        return self.donation_set.filter(
            order__status__in=[StatusDefinition.PLEDGED,
                               StatusDefinition.PENDING,
                               StatusDefinition.SUCCESS]
        ).distinct('order__user').count()

    @cached_property
    def sourcing(self):
        taskmembers = TaskMember.objects.filter(
            task__project=self,
            status__in=['applied', 'accepted', 'realized']
        ).distinct('member')
        return taskmembers.count()

    @property
    def supporters(self):
        return self.funding + self.sourcing


class BaseProjectPhaseLog(models.Model):
    project = models.ForeignKey('projects.Project')
    status = models.ForeignKey("bb_projects.ProjectPhase")
    start = CreationDateTimeField(
        _('created'), help_text=_('When this project entered in this status.'))

    class Meta():
        abstract = True


from projectwallmails import *
