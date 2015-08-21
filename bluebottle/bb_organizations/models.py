from django_iban.fields import IBANField, SWIFTBICField
from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from django_extensions.db.fields import (ModificationDateTimeField,
                                         CreationDateTimeField)
from django.db.models import options

from djchoices import DjangoChoices, ChoiceItem
from taggit.managers import TaggableManager

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('default_serializer',
                                                 'manage_serializer')


class BaseOrganizationMember(models.Model):
    """ Members from a Organization """

    class MemberFunctions(DjangoChoices):
        owner = ChoiceItem('owner', label=_('Owner'))
        editor = ChoiceItem('editor', label=_('Editor'))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('user'))
    function = models.CharField(_('function'),
                                max_length=20,
                                choices=MemberFunctions.choices)
    organization = models.ForeignKey(settings.ORGANIZATIONS_ORGANIZATION_MODEL,
                                     related_name="members")
    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('updated'))
    deleted = models.DateTimeField(_('deleted'), null=True, blank=True)

    class Meta:
        verbose_name = _('organization member')
        verbose_name_plural = _('organization members')
        abstract = True


class BaseOrganization(models.Model):
    """
    Organizations can run Projects. An organization has one or more members.
    """
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)

    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('updated'))
    deleted = models.DateTimeField(_('deleted'), null=True, blank=True)

    partner_organizations = models.TextField(_('partner organizations'),
                                             blank=True)

    # Address
    address_line1 = models.CharField(max_length=100, blank=True)
    address_line2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.ForeignKey('geo.Country', blank=True, null=True,
                                related_name='country')
    postal_code = models.CharField(max_length=20, blank=True)

    # Contact
    phone_number = models.CharField(_('phone number'), max_length=40,
                                    blank=True)
    website = models.URLField(_('website'), blank=True)

    email = models.EmailField(blank=True)

    tags = TaggableManager(blank=True, verbose_name=_('tags'))

    class Meta:
        abstract = True
        ordering = ['name']
        verbose_name = _('organization')
        verbose_name_plural = _('organizations')
        default_serializer = 'bluebottle.organizations.serializers.OrganizationSerializer'
        manage_serializer = 'bluebottle.organizations.serializers.ManageOrganizationSerializer'

    def __unicode__(self):
        return self.name

    def full_clean(self, exclude=None, validate_unique=False):
        if not self.slug:
            original_slug = slugify(self.name)
            slug = original_slug
            next_slug = 2
            while not slug or self.__class__.objects.filter(slug=slug):
                slug = '{0}-{1}'.format(original_slug, next_slug)
                next_slug += 1
            self.slug = slug
