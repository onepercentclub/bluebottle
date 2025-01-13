from __future__ import absolute_import
from builtins import str
from builtins import object
from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _

from future.utils import python_2_unicode_compatible

from bluebottle.utils.fields import ImageField
from bluebottle.utils.models import ValidatedModelMixin
from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection


@python_2_unicode_compatible
class Organization(ValidatedModelMixin, models.Model):
    """
    Organizations can run Projects. An organization has one or more members.
    """
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=100)
    description = models.TextField(_('description'), default='', blank=True)

    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('updated'), auto_now=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('owner'), null=True, on_delete=models.CASCADE
    )

    website = models.URLField(_('website'), blank=True)
    logo = ImageField(
        _('logo'),
        blank=True,
        help_text=_('Partner Organization Logo'),
        max_length=255,
        null=True,
        upload_to='partner_organization_logos/',

        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]
    )

    required_fields = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)

        super(Organization, self).save(*args, **kwargs)

    class Meta(object):
        ordering = ['name']
        verbose_name = _("partner organization")
        verbose_name_plural = _("partner organizations")

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
