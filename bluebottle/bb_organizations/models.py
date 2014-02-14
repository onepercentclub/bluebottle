from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from djchoices import DjangoChoices, ChoiceItem
from taggit_autocomplete_modified.managers import TaggableManagerAutocomplete as TaggableManager


class OrganizationMember(models.Model):
    """ Members from a Organization """

    class MemberFunctions(DjangoChoices):
        owner = ChoiceItem('owner', label=_('Owner'))
        editor = ChoiceItem('editor', label=_('Editor'))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('user'))
    function = models.CharField(_('function'), max_length=20, choices=MemberFunctions.choices)

    class Meta:
        verbose_name = _('organization member')
        verbose_name_plural = _('organization members')


class OrganizationDocument(models.Model):
    """ Document for an Organization """

    file = models.FileField(
        upload_to='organizations/documents', storage=FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT))
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('author'), blank=True, null=True)

    class Meta:
        verbose_name = _('organization document')
        verbose_name_plural = _('organization documents')

    @property
    def document_url(self):
        content_type = ContentType.objects.get_for_model(OrganizationDocument).id
        return reverse('document-download-detail', kwargs={'content_type': content_type, 'pk': self.pk})


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

    members = models.ManyToManyField('bb_organizations.OrganizationMember', null=True)
    documents = models.ManyToManyField('bb_organizations.OrganizationDocument', null=True)

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

    class Meta:
        abstract = True
        ordering = ['name']
        verbose_name = _('organization')
        verbose_name_plural = _('organizations')

    def __unicode__(self):
        return self.name

    def full_clean(self, exclude=None):
        if not self.slug:
            original_slug = slugify(self.name)
            slug = original_slug
            next_slug = 2
            while not slug or self.__class__.objects.filter(slug=slug):
                slug = '{0}{1}{2}'.format(original_slug, '-', next_slug)
                next_slug += 1
            self.slug = slug


