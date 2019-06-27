from django.db import models
from django.db.models.deletion import SET_NULL
from django.template.defaultfilters import slugify
from django.utils.html import format_html
from django.forms.models import model_to_dict
from django.utils.translation import ugettext_lazy as _
from djchoices.choices import DjangoChoices, ChoiceItem

from multiselectfield import MultiSelectField

from bluebottle.files.fields import ImageField
from bluebottle.fsm import FSMField, TransitionNotAllowed
from bluebottle.geo.models import Geolocation
from bluebottle.initiatives.messages import InitiativeClosedOwnerMessage, InitiativeApproveOwnerMessage
from bluebottle.organizations.models import Organization, OrganizationContact
from bluebottle.utils.models import BasePlatformSettings


class Initiative(models.Model):
    class Status(DjangoChoices):
        draft = ChoiceItem('draft', _('draft'))
        submitted = ChoiceItem('submitted', _('submitted'))
        needs_work = ChoiceItem('needs_work', _('needs work'))
        approved = ChoiceItem('approved', _('approved'))
        closed = ChoiceItem('closed', _('closed'))

    title = models.CharField(_('title'), max_length=255)

    status = FSMField(
        default=Status.draft,
        choices=Status.choices,
        protected=True
    )
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

    promoter = models.ForeignKey(
        'members.Member',
        verbose_name=_('promoter'),
        null=True,
    )

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

    place = models.ForeignKey(Geolocation, null=True, blank=True, on_delete=SET_NULL)
    location = models.ForeignKey('geo.Location', null=True, blank=True, on_delete=models.SET_NULL)

    has_organization = models.NullBooleanField(null=True, default=None)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=SET_NULL)
    organization_contact = models.ForeignKey(OrganizationContact, null=True, blank=True, on_delete=SET_NULL)

    def is_complete(self):
        from bluebottle.initiatives.serializers import InitiativeSubmitSerializer

        serializer = InitiativeSubmitSerializer(
            data=model_to_dict(self)
        )
        if not serializer.is_valid():
            return [unicode(error) for errors in serializer.errors.values() for error in errors]

    @status.transition(
        source=Status.draft,
        target=Status.submitted,
        conditions=[is_complete],
        custom={'button_name': _('submit')}
    )
    def submit(self):
        pass

    @status.transition(
        source=Status.needs_work,
        target=Status.submitted,
        conditions=[is_complete],
        custom={'button_name': _('resubmit')}
    )
    def resubmit(self):
        pass

    @status.transition(
        source=Status.submitted,
        target=Status.needs_work,
        custom={'button_name': _('needs work')}
    )
    def needs_work(self):
        pass

    @status.transition(
        source=Status.submitted,
        target=Status.approved,
        messages=[InitiativeApproveOwnerMessage],
        conditions=[is_complete],
        custom={'button_name': _('approve')}
    )
    def approve(self):
        for activity in self.activities.filter(status='draft'):
            activity.initiative = self
            try:
                activity.open()
                activity.save()
            except TransitionNotAllowed:
                pass

    @status.transition(
        source=[Status.approved, Status.submitted, Status.needs_work],
        target=Status.closed,
        messages=[InitiativeClosedOwnerMessage],
        custom={'button_name': _('close')}
    )
    def close(self):
        pass

    @status.transition(
        source=[Status.approved, Status.closed],
        target=Status.submitted,
        conditions=[is_complete],
        custom={'button_name': _('re-open')}
    )
    def reopen(self):
        pass

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

    class JSONAPIMeta:
        resource_name = 'initiatives'

    def __unicode__(self):
        return self.title

    @property
    def full_url(self):
        return format_html('/initiatives/details/{}/{}/', self.id, self.slug)

    def save(self, **kwargs):
        if self.slug in ['', 'new']:
            if self.title:
                self.slug = slugify(self.title)
            else:
                self.slug = 'new'
        super(Initiative, self).save(**kwargs)


class InitiativePlatformSettings(BasePlatformSettings):
    ACTIVITY_TYPES = (
        ('funding', _('Funding')),
        ('event', _('Events')),
        ('job', _('Jobs')),
    )

    activity_types = MultiSelectField(max_length=100, choices=ACTIVITY_TYPES)
    require_organization = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = _('initiative platform settings')
        verbose_name = _('initiative platform settings')
