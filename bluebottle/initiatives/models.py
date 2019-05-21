from django.db import models
from django.db.models.deletion import SET_NULL
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django_fsm import FSMField
from djchoices.choices import DjangoChoices, ChoiceItem

from multiselectfield import MultiSelectField

from bluebottle.files.fields import ImageField
from bluebottle.geo.models import InitiativePlace
from bluebottle.initiatives.messages import InitiativeClosedOwnerMessage, InitiativeApproveOwnerMessage, \
    InitiativeNeedsWorkOwnerMessage
from bluebottle.notifications.decorators import transition
from bluebottle.organizations.models import Organization, OrganizationContact
from bluebottle.utils.models import BasePlatformSettings


class Initiative(models.Model):
    class ReviewStatus(DjangoChoices):
        created = ChoiceItem('created', _('created'))
        submitted = ChoiceItem('submitted', _('submitted'))
        needs_work = ChoiceItem('needs_work', _('needs work'))
        approved = ChoiceItem('approved', _('approved'))
        cancelled = ChoiceItem('cancelled', _('cancelled'))
        rejected = ChoiceItem('rejected', _('rejected'))

    title = models.CharField(_('title'), max_length=255)

    status = FSMField(
        default=ReviewStatus.created,
        choices=ReviewStatus.choices,
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

    slug = models.SlugField(_('slug'), default='new', max_length=100)

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

    place = models.ForeignKey(InitiativePlace, null=True, blank=True, on_delete=SET_NULL)
    has_organization = models.NullBooleanField(null=True, default=None)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=SET_NULL)
    organization_contact = models.ForeignKey(OrganizationContact, null=True, blank=True, on_delete=SET_NULL)

    @transition(
        field='status',
        source=ReviewStatus.created,
        target=ReviewStatus.submitted,
        form='bluebottle.initiatives.forms.InitiativeSubmitForm',
        custom={'button_name': _('submit')}
    )
    def submit(self, **kwargs):
        pass

    @transition(
        field='status',
        source=ReviewStatus.needs_work,
        target=ReviewStatus.submitted,
        form='bluebottle.initiatives.forms.InitiativeSubmitForm',
        custom={'button_name': _('resubmit')}
    )
    def resubmit(self, **kwargs):
        pass

    @transition(
        field='status',
        source=ReviewStatus.submitted,
        target=ReviewStatus.needs_work,
        messages=[InitiativeNeedsWorkOwnerMessage],
        form='bluebottle.initiatives.forms.InitiativeSubmitForm',
        custom={'button_name': _('needs work')}
    )
    def needs_work(self, **kwargs):
        pass

    @transition(
        field='status',
        source=ReviewStatus.submitted,
        target=ReviewStatus.approved,
        messages=[InitiativeApproveOwnerMessage],
        form='bluebottle.initiatives.forms.InitiativeSubmitForm',
        custom={'button_name': _('approve')}
    )
    def approve(self, **kwargs):
        pass

    @transition(
        field='status',
        source=ReviewStatus.submitted,
        target=ReviewStatus.rejected,
        messages=[InitiativeClosedOwnerMessage],
        form='bluebottle.initiatives.forms.InitiativeSubmitForm',
        custom={'button_name': _('reject')}
    )
    def reject(self, **kwargs):
        pass

    @transition(
        field='status',
        source=[ReviewStatus.approved, ReviewStatus.submitted, ReviewStatus.needs_work],
        target=ReviewStatus.cancelled,
        form='bluebottle.initiatives.forms.InitiativeSubmitForm',
        custom={'button_name': _('cancel')}
    )
    def cancel(self, **kwargs):
        pass

    @transition(
        field='status',
        source=[ReviewStatus.cancelled, ReviewStatus.approved, ReviewStatus.rejected],
        target=ReviewStatus.submitted,
        form='bluebottle.initiatives.forms.InitiativeSubmitForm',
        custom={'button_name': _('re-open')}
    )
    def reopen(self, **kwargs):
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

    def save(self, **kwargs):
        if self.slug == 'new' and self.title:
            self.slug = slugify(self.title)

        super(Initiative, self).save(**kwargs)


class InitiativePlatformSettings(BasePlatformSettings):
    ACTIVITY_TYPES = (
        ('funding', _('Funding')),
        ('event', _('Events')),
        ('job', _('Jobs')),
    )

    SHARE_OPTIONS = (
        ('twitter', _('Twitter')),
        ('facebook', _('Facebook')),
        ('facebookAtWork', _('Facebook at Work')),
        ('linkedin', _('LinkedIn')),
        ('whatsapp', _('Whatsapp')),
        ('email', _('Email')),
    )

    activity_types = MultiSelectField(max_length=100, choices=ACTIVITY_TYPES)
    require_organization = models.BooleanField(default=False)
    share_options = MultiSelectField(
        max_length=100, choices=SHARE_OPTIONS, blank=True
    )
    facebook_at_work_url = models.URLField(max_length=100, null=True, blank=True)

    class Meta:
        verbose_name_plural = _('initiative platform settings')
        verbose_name = _('initiative platform settings')
