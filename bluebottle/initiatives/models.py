from django.db import models
from django.db.models.deletion import SET_NULL
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from bluebottle.files.fields import ImageField
from bluebottle.geo.models import InitiativePlace
from bluebottle.organizations.models import Organization, OrganizationContact
from bluebottle.utils.models import ReviewModel


class Initiative(ReviewModel):
    title = models.CharField(_('title'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=100)

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
        if not self.slug:
            self.slug = slugify(self.title)

        super(Initiative, self).save(**kwargs)
