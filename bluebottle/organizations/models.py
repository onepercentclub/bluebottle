from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify
from django.core.files.storage import FileSystemStorage

from bluebottle.bb_organizations.models import BaseOrganization, \
    BaseOrganizationMember

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
    registration = models.FileField(upload_to='organizations/registrations',
                                    storage=FileSystemStorage(
                                        location=settings.PRIVATE_MEDIA_ROOT),
                                    null=True,
                                    blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = _("organization")
        verbose_name_plural = _("organizations")

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
