from bluebottle.bb_organizations.models import (BaseOrganization,
                                                BaseOrganizationDocument,
                                                BaseOrganizationMember)
from bluebottle.utils.models import Address
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from django_extensions.db.fields import (CreationDateTimeField,
                                         ModificationDateTimeField)
from django_iban.fields import IBANField, SWIFTBICField

from djchoices import ChoiceItem, DjangoChoices

GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_organization', 'change_organization', 'delete_organization',
        )
    }
}

class Organization(BaseOrganization):
    """
    Organizations can run Projects. An organization has one or more members.
    """
    registration = models.FileField(upload_to='organizations/registrations', storage=FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT), null=True, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = _("organization")
        verbose_name_plural = _("organizations")
        default_serializer = 'bluebottle.organizations.serializers.OrganizationSerializer'
        manage_serializer = 'bluebottle.organizations.serializers.ManageOrganizationSerializer'

    def full_clean(self, exclude=None, validate_unique=False):
        if not self.slug:
            original_slug = slugify(self.name)
            slug = original_slug
            next = 2
            while not slug or Organization.objects.filter(slug=slug):
                slug = '%s%s%s' % (original_slug, '-', next)
                next += 1
            self.slug = slug


class OrganizationMember(BaseOrganizationMember):
    pass


class OrganizationDocument(BaseOrganizationDocument):
    pass
