from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import (
    CreationDateTimeField, ModificationDateTimeField
)

from bluebottle.utils.fields import ImageField
from bluebottle.utils.models import ValidatedModelMixin


class Organization(ValidatedModelMixin, models.Model):
    """
    Organizations can run Projects. An organization has one or more members.
    """
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=100)
    description = models.TextField(_('description'), default='', blank=True)

    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('updated'))

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('owner'), null=True)

    website = models.URLField(_('website'), blank=True)
    logo = ImageField(_('logo'),
                      blank=True,
                      help_text=_('Partner Organization Logo'),
                      max_length=255,
                      null=True,
                      upload_to='partner_organization_logos/')

    required_fields = ['name', 'website']

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)

        super(Organization, self).save(*args, **kwargs)

    class Meta:
        ordering = ['name']
        verbose_name = _("partner organization")
        verbose_name_plural = _("partner organizations")


class OrganizationContact(ValidatedModelMixin, models.Model):
    """
    Basic details for an organization contact
    """
    name = models.TextField(_('name'), null=True, blank=True, max_length=100)
    email = models.EmailField(_('email'), null=True, blank=True, max_length=254)
    phone = models.TextField(_('phone'), null=True, blank=True, max_length=40)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('owner'))

    created = CreationDateTimeField(
        _('created'),
        help_text=_('When this contact was created.')
    )
    updated = ModificationDateTimeField(_('updated'))

    required_fields = ['name', 'email']

    class Meta:
        verbose_name = _('Partner Organization Contact')
        verbose_name_plural = _('Partner Organization Contacts')
