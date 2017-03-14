from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _
from django.core.files.storage import FileSystemStorage
from django_extensions.db.fields import (CreationDateTimeField,
                                         ModificationDateTimeField)

from bluebottle.bb_organizations.models import (BaseOrganization,
                                                BaseOrganizationMember)

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

    def merge(self, organizations):
        """ Merge `organizations` into the current organization.
        Makes sure that all foreign keys point to `this`.

        Deletes all organization models in `organization` after merging.
        """
        for organization in organizations:
            for member in organization.members.all():
                member.organization = self
                member.save()

            for project in organization.projects.all():
                project.organization = self
                project.save()

            organization.delete()

    class Meta:
        ordering = ['name']
        verbose_name = _("organization")
        verbose_name_plural = _("organizations")


class OrganizationContact(models.Model):
    """
    Basic details for an organization contact
    """
    name = models.TextField(_('name'), max_length=100)
    email = models.EmailField(_('email'), max_length=254)
    phone = models.TextField(_('phone'), max_length=40)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('user'))
    organization = models.ForeignKey('organizations.Organization',
                                     related_name="contacts")
    created = CreationDateTimeField(
        _('created'), help_text=_('When this contact was created.'))
    updated = ModificationDateTimeField(_('updated'))


class OrganizationMember(BaseOrganizationMember):
    pass
