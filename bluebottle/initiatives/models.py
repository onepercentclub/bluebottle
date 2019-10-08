from django.db import models
from django.db.models import Max
from django.db.models.deletion import SET_NULL
from django.template.defaultfilters import slugify
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from multiselectfield import MultiSelectField

from bluebottle.files.fields import ImageField
from bluebottle.fsm import FSMField, TransitionManager, TransitionsMixin
from bluebottle.geo.models import Geolocation, Location
from bluebottle.initiatives.transitions import InitiativeReviewTransitions
from bluebottle.organizations.models import Organization, OrganizationContact
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
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=SET_NULL)
    organization_contact = models.ForeignKey(OrganizationContact, null=True, blank=True, on_delete=SET_NULL)

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
    def required_fields(self):
        fields = [
            'title', 'pitch', 'owner',
            'has_organization', 'story', 'image',
            'theme',
        ]

        if self.has_organization:
            fields += ['organization', 'organization_contact']

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

        if self.has_organization:
            if not self.organization and self.owner and self.owner.partner_organization:
                self.organization = self.owner.partner_organization

        super(Initiative, self).save(**kwargs)


class InitiativePlatformSettings(BasePlatformSettings):
    ACTIVITY_TYPES = (
        ('funding', _('Funding')),
        ('event', _('Events')),
        ('assignment', _('Assignment')),
    )

    activity_types = MultiSelectField(max_length=100, choices=ACTIVITY_TYPES)
    require_organization = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = _('initiative platform settings')
        verbose_name = _('initiative platform settings')
