from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _
from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from django.db.models import options

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('default_serializer', 'preview_serializer', 'manage_serializer')


GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_donation', 'change_donation', 'delete_donation',
        )
    }
}


class Donation(models.Model):
    """
    Donation of an amount from a user to a project.
    """
    amount = models.DecimalField(_("Amount"), max_digits=16, decimal_places=2)

    project = models.ForeignKey(settings.PROJECTS_PROJECT_MODEL, verbose_name=_("Project"))
    fundraiser = models.ForeignKey(settings.FUNDRAISERS_FUNDRAISER_MODEL, verbose_name=_("Fundraiser"), null=True, blank=True)
    order = models.ForeignKey(settings.ORDERS_ORDER_MODEL, verbose_name=_("Order"), related_name='donations', null=True, blank=True)

    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))
    completed = models.DateTimeField(_("Ready"), blank=True, editable=False, null=True)

    anonymous = models.BooleanField(_("Anonymous"), default=False)

    @property
    def status(self):
        return self.order.status

    @property
    def user(self):
        return self.order.user

    @property
    def public_user(self):
        if self.anonymous:
            return None
        return self.user

    class Meta:
        default_serializer = 'bluebottle.donations.serializers.DefaultDonationSerializer'
        preview_serializer = 'bluebottle.donations.serializers.PreviewDonationSerializer'
        manage_serializer = 'bluebottle.donations.serializers.ManageDonationSerializer'

import signals
