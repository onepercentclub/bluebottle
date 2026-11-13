from __future__ import absolute_import

from builtins import object
from builtins import str

from colorfield.fields import ColorField
from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _
from django_quill.fields import QuillField
from future.utils import python_2_unicode_compatible
from parler.models import TranslatableModel, TranslatedFields

from bluebottle.cms.utils.color_contrast import choose_on_color
from bluebottle.cms.utils.color_contrast import ensure_readable_fill
from bluebottle.utils.fields import ImageField
from bluebottle.utils.models import ValidatedModelMixin
from bluebottle.utils.utils import get_current_host, get_current_language
from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection


@python_2_unicode_compatible
class Organization(ValidatedModelMixin, TranslatableModel, models.Model):
    """
    Organizations can run Projects. An organization has one or more members.
    """
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=100)
    translations = TranslatedFields(
        slogan=models.CharField(
            _('Slogan'), max_length=255, null=True, blank=True,
            help_text=_(
                'A short sentence to explain your organisation. This sentence is directly visible on the page.'
            )),
        story=QuillField(
            _('Story'), blank=True, null=True,
            help_text=_(
                'A more detailed story about your organisation. This story can be accessed via a link on the page.'
            )
        )
    )

    created = models.DateTimeField(_('Created'), auto_now_add=True)
    updated = models.DateTimeField(_('Updated'), auto_now=True)

    verified = models.BooleanField(_('Verified'), default=False)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('owner'), null=True, on_delete=models.CASCADE
    )

    origin = models.ForeignKey(
        'activity_pub.Organization', null=True, related_name="organizations", on_delete=models.SET_NULL
    )

    website = models.URLField(_('website'), blank=True)
    logo = ImageField(
        _('Logo'),
        blank=True,
        help_text=_('Organization logo'),
        max_length=5000,
        null=True,
        upload_to='organizations/',

        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]
    )
    image = ImageField(
        _('Main image'),
        blank=True,
        help_text=_('Organization image'),
        max_length=5000,
        null=True,
        upload_to='organizations/',

        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]
    )
    color = ColorField(
        _('Colour'),
        null=True,
        blank=True,
        help_text=_('Background colour for the organisation page header.'),
    )

    required_fields = ['name']

    def __str__(self):
        if self.verified:
            return f'{self.name} (verified)'
        else:
            return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)

        super(Organization, self).save(*args, **kwargs)

    def get_absolute_url(self):
        domain = get_current_host()
        language = get_current_language()
        return u"{}/{}/organizations/{}/{}/activities/list".format(
            domain, language,
            self.pk,
            self.slug
        )

    @property
    def background_color(self):
        from bluebottle.cms.models import SitePlatformSettings

        if not self.color:
            return None

        platform = SitePlatformSettings.load()
        if platform.accessible_colours:
            return ensure_readable_fill(self.color) or self.color
        return self.color

    @property
    def text_color(self):
        return choose_on_color(self.background_color)

    @property
    def activity_pub_url(self):
        from bluebottle.activity_pub.models import Organization as ActivityPubOrganization
        try:
            return self.activity_pub_organization.iri
        except ActivityPubOrganization.DoesNotExist:
            return None

    class Meta(object):
        ordering = ['name']
        verbose_name = _("organisation")
        verbose_name_plural = _("organisations")

    class JSONAPIMeta:
        resource_name = 'organizations'


class OrganizationContact(ValidatedModelMixin, models.Model):
    """
    Basic details for an organization contact
    """
    name = models.TextField(_('name'), null=True, blank=True, max_length=100)
    email = models.EmailField(_('email'), null=True, blank=True, max_length=254)
    phone = models.TextField(_('phone'), null=True, blank=True, max_length=40)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('owner'), null=True, on_delete=models.CASCADE
    )

    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('updated'), auto_now=True)

    required_fields = []

    class Meta(object):
        verbose_name = _('Partner Organization Contact')
        verbose_name_plural = _('Partner Organization Contacts')

    def __str__(self):
        return str(self.name)
