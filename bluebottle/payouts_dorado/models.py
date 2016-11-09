from bluebottle.utils.fields import MoneyField
from django.db import models
from django_extensions.db.fields import (ModificationDateTimeField,
                                         CreationDateTimeField)
from django.utils.translation import ugettext as _


class Payout(models.Model):
    """
    Local representations of payouts. Actual payouts are handled by
    Dorado (Payout Service)
    """

    PAYOUT_STATUSES = (
        ('new', _('New')),
        ('in_progress', _('In progress')),
        ('settled', _('Settled')),
        ('failed', _('Failed')),
    )

    project = models.ForeignKey('projects.Project')
    status = models.CharField(max_length=30,
                              choices=PAYOUT_STATUSES,
                              default='new')
    amount = MoneyField()
    remote_id = models.CharField(max_length=200, null=True)
    created = CreationDateTimeField(_("created"))
    updated = ModificationDateTimeField(_("updated"))
    settled = models.DateTimeField(null=True)


from .signals import *  # noqa