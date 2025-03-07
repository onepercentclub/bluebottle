from builtins import object
from builtins import str

from adminsortable.models import SortableMixin
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, connection
from django.db.models import Max
from django.db.models.deletion import SET_NULL
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.functional import lazy
from django.utils.translation import gettext_lazy as _
from future.utils import python_2_unicode_compatible
from multiselectfield import MultiSelectField
from parler.models import TranslatedFields
from djchoices import DjangoChoices, ChoiceItem

from django_quill.fields import QuillField

from bluebottle.files.fields import ImageField
from bluebottle.follow.models import Follow
from bluebottle.fsm.triggers import TriggerMixin
from bluebottle.geo.models import Geolocation
from bluebottle.initiatives.validators import UniqueTitleValidator
from bluebottle.offices.models import OfficeRestrictionChoices
from bluebottle.organizations.models import Organization, OrganizationContact
from bluebottle.segments.models import SegmentType
from bluebottle.utils.models import BasePlatformSettings, ValidatedModelMixin, \
    SortableTranslatableModel
from bluebottle.utils.utils import get_current_host, get_current_language


@python_2_unicode_compatible
class Initiative(TriggerMixin, ValidatedModelMixin, models.Model):
    status = models.CharField(max_length=40)
    title = models.CharField(
        _('title'),
        blank=True,
        max_length=255)

    owner = models.ForeignKey(
        'members.Member',
        verbose_name=_('owner'),
        related_name='own_%(class)ss',
        on_delete=models.CASCADE
    )

    reviewer = models.ForeignKey(
        'members.Member',
        null=True,
        blank=True,
        verbose_name=_('reviewer'),
        related_name='review_%(class)ss',
        on_delete=models.SET_NULL
    )

    activity_manager = models.ForeignKey(
        'members.Member',
        null=True,
        blank=True,
        verbose_name=_('co-initiator'),
        help_text=_('The co-initiator can create and edit activities for '
                    'this initiative, but cannot edit the initiative itself.'),
        related_name='activity_manager_%(class)ss',
        on_delete=models.SET_NULL
    )

    activity_managers = models.ManyToManyField(
        'members.Member',
        blank=True,
        verbose_name=_('co-initiators'),
        help_text=_('Co-initiators can create and edit activities for '
                    'this initiative, but cannot edit the initiative itself.'),
        related_name='activity_managers_%(class)ss',
    )
    promoter = models.ForeignKey(
        'members.Member',
        verbose_name=_('promoter'),
        blank=True,
        null=True,
        related_name='promoter_%(class)ss',
        on_delete=models.SET_NULL
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    has_deleted_data = models.BooleanField(
        default=False
    )

    slug = models.SlugField(_('slug'), max_length=100, default='new')

    pitch = models.TextField(
        _('pitch'), help_text=_('Pitch your smart idea in one sentence'),
        blank=True
    )
    story = QuillField(_('story'), blank=True)

    theme = models.ForeignKey('initiatives.Theme', null=True, blank=True, on_delete=SET_NULL)
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
        'geo.Location', verbose_name=_('office'),
        null=True, blank=True, on_delete=models.SET_NULL)

    is_global = models.BooleanField(
        verbose_name=_('is global'),
        help_text=_(
            'Global initiatives do not have a location. '
            'Instead the location is stored on the respective activities.'
        ),
        default=False
    )

    has_organization = models.BooleanField(null=True, default=False)

    organization = models.ForeignKey(
        Organization,
        null=True,
        blank=True,
        on_delete=SET_NULL,
        related_name='initiatives'
    )
    organization_contact = models.ForeignKey(OrganizationContact, null=True, blank=True, on_delete=SET_NULL)
    is_open = models.BooleanField(
        verbose_name=_("Is open"),
        help_text=_("Any authenticated users can start an activity under this initiative."),
        default=False,
    )

    follows = GenericRelation(Follow, object_id_field='instance_id')

    class Meta(object):
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

    class JSONAPIMeta(object):
        resource_name = 'initiatives'

    def __str__(self):
        return self.title or str(_('-empty-'))

    @property
    def position(self):
        if self.place and self.place.position:
            return self.place.position
        if self.location and self.location.position:
            return self.location.position

    @property
    def required_fields(self):
        fields = [
            'title', 'pitch', 'owner',
            'has_organization', 'story.html', 'image',
            'theme',
        ]

        return fields

    validators = [UniqueTitleValidator]

    def get_absolute_url(self):
        domain = get_current_host()
        language = get_current_language()
        link = '{}/{}/initiatives/details/{}/{}'.format(domain, language, self.id, self.slug)
        return link

    def get_admin_url(self):
        domain = get_current_host()
        url = reverse('admin:initiatives_initiative_change', args=(self.id,))
        link = '{}{}'.format(domain, url)
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


ACTIVITY_SEARCH_FILTERS = (
    ('country', _('Country')),
    ('date', _('Date')),
    ('distance', _('Distance')),
    ('is_online', _('Online / In-person')),
    ('skill', _('Skill')),
    ('team_activity', _('Individual / Team')),
    ('theme', _('Theme')),
    ('category', _('Category')),
    ('office', _('Office')),
    ('office_subregion', _('Office group')),
    ('office_region', _('Office region')),
)


INITIATIVE_SEARCH_FILTERS = (
    ('office', _('Office')),
    ('country', _('Country')),
    ('theme', _('Theme')),
    ('category', _('Category')),
)


def get_search_filters(filters):
    if connection.tenant.schema_name != 'public':
        for segment in SegmentType.objects.all():
            filters = filters + ((f'segment.{segment.slug}', segment.name),)
    return filters


class CreateFlowChoices(DjangoChoices):
    initiative = ChoiceItem(
        'initiative',
        label=_("Start the create flow by creating an initiative")
    )
    acitivity = ChoiceItem(
        'activity',
        label=_("Directly create an activity")
    )


class InitiativePlatformSettings(BasePlatformSettings):
    ACTIVITY_TYPES = (
        ("funding", _("Funding")),
        ("periodactivity", _("Activity during a period")),
        ("dateactivity", _("Activity on a specific date")),
        ("deadlineactivity", _("Activity within a deadline")),
        ("scheduleactivity", _("Scheduled activity")),
        ("periodicactivity", _("Periodic Activity")),
        ("deed", _("Deed")),
        ("collect", _("Collect activity")),
    )
    CONTACT_OPTIONS = (
        ('mail', _('E-mail')),
        ('phone', _('Phone')),
    )

    activity_types = MultiSelectField(max_length=300, choices=ACTIVITY_TYPES)
    team_activities = models.BooleanField(
        default=False,
        help_text=_("Enable team activities where teams sign-up instead of individuals.")
    )
    require_organization = models.BooleanField(
        default=False,
        help_text=_("Require initiators to specify a partner organisation when creating an initiative.")
    )
    initiative_search_filters = MultiSelectField(max_length=1000, choices=INITIATIVE_SEARCH_FILTERS)
    activity_search_filters = MultiSelectField(
        _('Activity search: more filters'),
        max_length=1000, default=[], choices=ACTIVITY_SEARCH_FILTERS
    )
    contact_method = models.CharField(max_length=100, choices=CONTACT_OPTIONS, default='mail')

    include_full_activities = models.BooleanField(
        default=True,
        help_text=_("Include full activities in upcoming activities list")
    )

    enable_impact = models.BooleanField(
        default=False,
        help_text=_("Allow activity managers to indicate the impact they make.")
    )

    enable_office_regions = models.BooleanField(
        default=False,
        help_text=_("Allow admins to add (sub)regions to their offices.")
    )

    enable_office_restrictions = models.BooleanField(
        default=False,
        help_text=_("Allow activity managers to specify office restrictions on activities.")
    )
    default_office_restriction = models.CharField(
        _('Default office restriction'),
        default=OfficeRestrictionChoices.all,
        choices=OfficeRestrictionChoices.choices,
        blank=True, null=True, max_length=100
    )

    enable_multiple_dates = models.BooleanField(
        default=False,
        help_text=_("Enable date activities to have multiple slots.")
    )
    enable_open_initiatives = models.BooleanField(
        default=False,
        help_text=_("Allow admins to open up initiatives for any user to add activities.")
    )
    enable_participant_exports = models.BooleanField(
        default=False,
        help_text=_("Add a link to activities so managers van download a contributor list.")
    )
    enable_matching_emails = models.BooleanField(
        _('Enable matching'),
        default=False,
        help_text=_((
            "Users will be able to set their preferences for a personalised activity overview "
            "and receive monthly emails with activities that best suit them."
        ))
    )

    create_flow = models.CharField(
        _('Create flow'),
        default=CreateFlowChoices.initiative,
        choices=CreateFlowChoices.choices,
        max_length=100
    )

    @property
    def deeds_enabled(self):
        return 'deed' in self.activity_types

    @property
    def collect_enabled(self):
        return 'collect' in self.activity_types

    @property
    def funding_enabled(self):
        return 'funding' in self.activity_types

    class Meta(object):
        verbose_name_plural = _('initiative settings')
        verbose_name = _('initiative settings')


class SearchFilter(SortableMixin, models.Model):

    settings = models.ForeignKey(
        InitiativePlatformSettings,
        related_name='search_filters',
        on_delete=models.deletion.CASCADE
    )
    highlight = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    @property
    def placeholder(self):
        if self.type == 'office':
            return _('Select an office')
        if self.type in ['is_online', 'team_activity']:
            return _('Make a choice')
        return _('Select a {filter_name}').format(filter_name=self.name.lower())

    class Meta:
        abstract = True
        ordering = ['order']


class ActivitySearchFilter(SearchFilter):
    type = models.CharField(max_length=100, choices=lazy(get_search_filters, tuple)(ACTIVITY_SEARCH_FILTERS))

    @property
    def name(self):
        filters = [filter[1] for filter in get_search_filters(ACTIVITY_SEARCH_FILTERS) if filter[0] == self.type]
        if len(filters):
            return filters[0]
        return '--------'

    settings = models.ForeignKey(
        InitiativePlatformSettings,
        related_name='search_filters_activities',
        on_delete=models.deletion.CASCADE
    )


class InitiativeSearchFilter(SearchFilter):
    type = models.CharField(max_length=100, choices=lazy(get_search_filters, tuple)(INITIATIVE_SEARCH_FILTERS))

    @property
    def name(self):
        filters = [filter[1] for filter in get_search_filters(INITIATIVE_SEARCH_FILTERS) if filter[0] == self.type]
        if len(filters):
            return filters[0]
        return '--------'

    settings = models.ForeignKey(
        InitiativePlatformSettings,
        related_name='search_filters_initiatives',
        on_delete=models.deletion.CASCADE
    )


class Theme(SortableTranslatableModel):
    """ Themes for initiatives. """
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    disabled = models.BooleanField(_('disabled'), default=False)

    translations = TranslatedFields(
        name=models.CharField(_('name'), max_length=100),
        description=models.TextField(_('description'), blank=True)
    )

    def __str__(self):
        return self.name

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super(Theme, self).save(**kwargs)

    class Meta(object):
        verbose_name = _('theme')
        verbose_name_plural = _('themes')
        permissions = (
            ('api_read_theme', 'Can view theme through API'),
        )

    class JSONAPIMeta(object):
        resource_name = 'themes'
