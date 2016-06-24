from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _
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


class OrganizationMember(BaseOrganizationMember):
    pass
