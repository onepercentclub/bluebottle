from django.db import models
from django.db.models import Max
from django.db.models.deletion import SET_NULL
from django.contrib.contenttypes.fields import GenericRelation
from django.template.defaultfilters import slugify
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from moneyed import Money

from multiselectfield import MultiSelectField

from bluebottle.clients import properties
from bluebottle.files.fields import ImageField
from bluebottle.fsm import FSMField, TransitionManager, TransitionsMixin
from bluebottle.follow.models import Follow
from bluebottle.geo.models import Geolocation, Location
from bluebottle.initiatives.transitions import InitiativeReviewTransitions
from bluebottle.organizations.models import Organization, OrganizationContact
from bluebottle.utils.exchange_rates import convert
from bluebottle.utils.models import BasePlatformSettings, Validator, ValidatedModelMixin
from bluebottle.utils.utils import get_current_host, get_current_language


class UniqueTitleValidator(Validator):
    field = 'title'
    code = 'required'
    message = _('The title must be unique')

    def is_valid(self):
        return not Initiative.objects.exclude(
            pk=self.instance.pk
        ).filter(
            status='approved', title=self.instance.title
        )


class Initiative(TransitionsMixin, ValidatedModelMixin, models.Model):
    status = FSMField(
        default=InitiativeReviewTransitions.values.draft,
        choices=InitiativeReviewTransitions.values.choices,
        protected=True
    )

    title = models.CharField(_('title'), max_length=255)

    owner = models.ForeignKey(
        'members.Member',
        verbose_name=_('owner'),
        related_name='own_%(class)ss',
    )

    reviewer = models.ForeignKey(
        'members.Member',
        null=True,
        blank=True,
        verbose_name=_('reviewer'),
        related_name='review_%(class)ss',
    )

    activity_manager = models.ForeignKey(
        'members.Member',
        null=True,
        blank=True,
        verbose_name=_('activity manager'),
        related_name='activity_manager_%(class)ss',
    )

    promoter = models.ForeignKey(
        'members.Member',
        verbose_name=_('promoter'),
        blank=True,
        null=True,
        related_name='promoter_%(class)ss',
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    slug = models.SlugField(_('slug'), max_length=100, default='new')

    pitch = models.TextField(
        _('pitch'), help_text=_('Pitch your smart idea in one sentence'),
        blank=True
    )
    story = models.TextField(_('story'), blank=True)

    theme = models.ForeignKey('bb_projects.ProjectTheme', null=True, blank=True, on_delete=SET_NULL)
    categories = models.ManyToManyField('categories.Category', blank=True)

    image = ImageField(blank=True, null=True)

    video_url = models.URLField(
        _('video'),
        max_length=100,
        blank=True,
        null=True,
        default='',
        help_text=_(
            "Do you have a video pitch or a short movie that "
            "explains your initiative? Cool! We can't wait to see it! "
            "You can paste the link to YouTube or Vimeo video here"
        )
    )

    place = models.ForeignKey(
        Geolocation, verbose_name=_('Impact location'),
        null=True, blank=True, on_delete=SET_NULL)

    location = models.ForeignKey(
        'geo.Location', verbose_name=_('Office location'),
        null=True, blank=True, on_delete=models.SET_NULL)

    has_organization = models.NullBooleanField(null=True, default=None)

    organization = models.ForeignKey(
        Organization,
        null=True,
        blank=True,
        on_delete=SET_NULL,
        related_name='initiatives'
    )
    organization_contact = models.ForeignKey(OrganizationContact, null=True, blank=True, on_delete=SET_NULL)

    follows = GenericRelation(Follow, object_id_field='instance_id')

    class Meta:
        verbose_name = _("Initiative")
        verbose_name_plural = _("Initiatives")
        permissions = (
            ('api_read_initiative', 'Can view initiative through the API'),
            ('api_add_initiative', 'Can add initiative through the API'),
            ('api_change_initiative', 'Can change initiative through the API'),
            ('api_delete_initiative', 'Can delete initiative through the API'),

            ('api_read_own_initiative', 'Can view own initiative through the API'),
            ('api_add_own_initiative', 'Can add own initiative through the API'),
            ('api_change_own_initiative', 'Can change own initiative through the API'),
            ('api_change_own_running_initiative', 'Can change own initiative through the API'),
            ('api_delete_own_initiative', 'Can delete own initiative through the API'),
        )

    transitions = TransitionManager(InitiativeReviewTransitions, 'status')

    class JSONAPIMeta:
        resource_name = 'initiatives'

    def __unicode__(self):
        return self.title or str(_('-empty-'))

    @property
    def position(self):
        if self.place and self.place.position:
            return self.place.position
        if self.location and self.location.position:
            return self.location.position

    @property
    def stats(self):
        activities = self.activities.filter(status='succeeded')
        stats = [activity.stats for activity in activities]
        currency = properties.DEFAULT_CURRENCY

        return {
            'activities': len(activities),
            'contributions': sum(stat['count'] for stat in stats),
            'hours': sum(stat['hours'] or 0 for stat in stats if 'hours' in stat),
            'amount': sum(
                convert(Money(stat['amount']['amount'], stat['amount']['currency']), currency).amount
                for stat in stats if 'amount' in stat
            ),
        }

    @property
    def required_fields(self):
        fields = [
            'title', 'pitch', 'owner',
            'has_organization', 'story', 'image',
            'theme',
        ]

        if self.has_organization:
            fields.append('organization')

            if not self.owner.partner_organization:
                fields.append('organization_contact')

        if Location.objects.count():
            fields.append('location')
        else:
            fields.append('place')

        return fields

    validators = [UniqueTitleValidator]

    def get_absolute_url(self):
        domain = get_current_host()
        language = get_current_language()
        link = format_html('{}/{}/initiatives/details/{}/{}', domain, language, self.id, self.slug)
        return link

    def save(self, **kwargs):
        if self.slug in ['', 'new']:
            if self.title and slugify(self.title):
                self.slug = slugify(self.title)
                if not self.slug:
                    # If someone uses only special chars as title then construct a slug
                    self.slug = 'in-{}'.format(self.__class__.objects.all().aggregate(Max('id'))['id__max'] or 0 + 1)
            else:
                self.slug = 'new'

        if not self.activity_manager:
            self.activity_manager = self.owner

        try:
            if InitiativePlatformSettings.objects.get().require_organization:
                self.has_organization = True
        except InitiativePlatformSettings.DoesNotExist:
            pass

        if not self.organization \
                and self.owner \
                and self.owner.partner_organization \
                and self.has_organization is not False:
            self.has_organization = True
            self.organization = self.owner.partner_organization

        if self.has_organization is None and (self.organization or self.organization_contact):
            self.has_organization = True

        if self.has_organization is False:
            self.organization = None
            self.organization_contact = None

        super(Initiative, self).save(**kwargs)


class InitiativePlatformSettings(BasePlatformSettings):
    ACTIVITY_TYPES = (
        ('funding', _('Funding')),
        ('event', _('Events')),
        ('assignment', _('Assignment')),
    )
    ACTIVITY_SEARCH_FILTERS = (
        ('location', _('Office location')),
        ('country', _('Country')),
        ('date', _('Date')),
        ('skill', _('Skill')),
        ('type', _('Type')),
        ('theme', _('Theme')),
        ('category', _('Category')),
        ('status', _('Status')),
    )
    INITIATIVE_SEARCH_FILTERS = (
        ('location', _('Office location')),
        ('country', _('Country')),
        ('theme', _('Theme')),
        ('category', _('Category')),
    )
    CONTACT_OPTIONS = (
        ('mail', _('E-mail')),
        ('phone', _('Phone')),
    )

    activity_types = MultiSelectField(max_length=100, choices=ACTIVITY_TYPES)
    require_organization = models.BooleanField(default=False)
    initiative_search_filters = MultiSelectField(max_length=1000, choices=INITIATIVE_SEARCH_FILTERS)
    activity_search_filters = MultiSelectField(max_length=1000, choices=ACTIVITY_SEARCH_FILTERS)
    contact_method = models.CharField(max_length=100, choices=CONTACT_OPTIONS, default='mail')

    class Meta:
        verbose_name_plural = _('initiative settings')
        verbose_name = _('initiative settings')


from bluebottle.initiatives.wallposts import *  # noqa
