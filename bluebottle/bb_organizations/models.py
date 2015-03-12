from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import options
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from django_extensions.db.fields import (CreationDateTimeField,
                                         ModificationDateTimeField)
from django_iban.fields import IBANField, SWIFTBICField
from taggit.managers import TaggableManager

from djchoices import ChoiceItem, DjangoChoices

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('default_serializer', 'manage_serializer')


class BaseOrganizationMember(models.Model):
    """ Members from a Organization """

    class MemberFunctions(DjangoChoices):
        owner = ChoiceItem('owner', label=_('Owner'))
        editor = ChoiceItem('editor', label=_('Editor'))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('user'))
    function = models.CharField(_('function'), max_length=20, choices=MemberFunctions.choices)
    organization = models.ForeignKey(settings.ORGANIZATIONS_ORGANIZATION_MODEL, related_name="members")
    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('updated'))

    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('updated'))
    deleted = models.DateTimeField(_('deleted'), null=True, blank=True)

    class Meta:
        verbose_name = _('organization member')
        verbose_name_plural = _('organization members')
        abstract = True


class BaseOrganizationDocument(models.Model):
    """ Document for an Organization """

    file = models.FileField(
        upload_to='organizations/documents')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('author'), blank=True, null=True)
    organization = models.ForeignKey(settings.ORGANIZATIONS_ORGANIZATION_MODEL, related_name="documents")
    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('updated'))

    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('updated'))
    deleted = models.DateTimeField(_('deleted'), null=True, blank=True)

    class Meta:
        verbose_name = _('organization document')
        verbose_name_plural = _('organization documents')
        abstract = True

    @property
    def document_url(self):
        from bluebottle.utils.model_dispatcher import get_organizationdocument_model
        document_model = get_organizationdocument_model()
        content_type = ContentType.objects.get_for_model(document_model).id
        # pk may be unset if not saved yet, in which case no url can be
        # generated.
        if self.pk is not None:
            return reverse('document_download_detail', kwargs={'content_type': content_type, 'pk': self.pk or 1})
        return None

class BaseOrganization(models.Model):
    """
    Organizations can run Projects. An organization has one or more members.
    """
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)

    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('updated'))
    deleted = models.DateTimeField(_('deleted'), null=True, blank=True)

    partner_organizations = models.TextField(_('partner organizations'), blank=True)

    # Address
    address_line1 = models.CharField(max_length=100, blank=True)
    address_line2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.ForeignKey('geo.Country', blank=True, null=True, related_name='country')
    postal_code = models.CharField(max_length=20, blank=True)

    # Contact
    phone_number = models.CharField(_('phone number'), max_length=40, blank=True)
    website = models.URLField(_('website'), blank=True)

    email = models.EmailField(blank=True)
    twitter = models.CharField(_('twitter'), max_length=255, blank=True)
    facebook = models.CharField(_('facebook'), max_length=255, blank=True)
    skype = models.CharField(_('skype'), max_length=255, blank=True)

    tags = TaggableManager(blank=True, verbose_name=_('tags'))

    #Account holder Info
    account_holder_name = models.CharField(_("account holder name"), max_length=255, blank=True)
    account_holder_address = models.CharField(_("account holder address"), max_length=255, blank=True)
    account_holder_postal_code = models.CharField(_("account holder postal code"), max_length=20, blank=True)
    account_holder_city = models.CharField(_("account holder city"), max_length=255, blank=True)
    account_holder_country = models.ForeignKey('geo.Country', blank=True, null=True, related_name="account_holder_country")

    #Bank details
    account_iban = IBANField(_("account IBAN"), blank=True)
    account_bic = SWIFTBICField(_("account SWIFT-BIC"), blank=True)
    account_number = models.CharField(_("account number"), max_length=255, blank=True)
    account_bank_name = models.CharField(_("account bank name"), max_length=255, blank=True)
    account_bank_address = models.CharField(_("account bank address"), max_length=255, blank=True)
    account_bank_postal_code = models.CharField(_("account bank postal code"), max_length=20, blank=True)
    account_bank_city = models.CharField(_("account bank city"), max_length=255, blank=True)
    account_bank_country = models.ForeignKey('geo.Country', blank=True, null=True, related_name="account_bank_country")
    account_other = models.CharField(_("account information that doesn't fit in the other field"), max_length=255, blank=True)


    class Meta:
        abstract = True
        ordering = ['name']
        verbose_name = _('organization')
        verbose_name_plural = _('organizations')
        default_serializer = 'bluebottle.bb_organizations.serializers.OrganizationSerializer'
        manage_serializer = 'bluebottle.bb_organizations.serializers.ManageOrganizationSerializer'

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
