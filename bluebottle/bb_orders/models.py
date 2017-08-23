from django.conf import settings
from django.db import models
from django.db.models.aggregates import Sum
from django.utils.timezone import now
from django.utils.translation import ugettext as _

from django_extensions.db.fields import (ModificationDateTimeField,
                                         CreationDateTimeField)
from django_fsm import FSMField, transition
from moneyed.classes import Money

from bluebottle.donations.models import Donation
from bluebottle.utils.fields import MoneyField
from bluebottle.utils.utils import FSMTransition, StatusDefinition


class BaseOrder(models.Model, FSMTransition):
    """
    An Order is a collection of Donations with one or more OrderPayments
    referring to it.
    """
    # Mapping the Order Payment Status to the Order Status
    STATUS_MAPPING = {
        StatusDefinition.CREATED: StatusDefinition.LOCKED,
        StatusDefinition.STARTED: StatusDefinition.LOCKED,
        StatusDefinition.PLEDGED: StatusDefinition.PLEDGED,
        StatusDefinition.AUTHORIZED: StatusDefinition.PENDING,
        StatusDefinition.SETTLED: StatusDefinition.SUCCESS,
        StatusDefinition.CHARGED_BACK: StatusDefinition.FAILED,
        StatusDefinition.REFUNDED: StatusDefinition.FAILED,
        StatusDefinition.FAILED: StatusDefinition.FAILED,
        StatusDefinition.UNKNOWN: StatusDefinition.FAILED
    }

    STATUS_CHOICES = (
        (StatusDefinition.CREATED, _('Created')),
        (StatusDefinition.LOCKED, _('Locked')),
        (StatusDefinition.PLEDGED, _('Pledged')),
        (StatusDefinition.PENDING, _('Pending')),
        (StatusDefinition.SUCCESS, _('Success')),
        (StatusDefinition.FAILED, _('Failed')),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("user"),
                             blank=True, null=True)
    status = FSMField(default=StatusDefinition.CREATED, choices=STATUS_CHOICES,
                      protected=True)

    order_type = models.CharField(max_length=100, default='one-off')

    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))
    confirmed = models.DateTimeField(_("Confirmed"), blank=True, editable=False,
                                     null=True)
    completed = models.DateTimeField(_("Completed"), blank=True, editable=False,
                                     null=True)

    total = MoneyField(_("Amount"), )

    @property
    def owner(self):
        return self.user

    @transition(field=status,
                source=[StatusDefinition.PLEDGED, StatusDefinition.CREATED,
                        StatusDefinition.FAILED],
                target=StatusDefinition.LOCKED)
    def locked(self):
        pass

    @transition(field=status,
                source=[StatusDefinition.LOCKED, StatusDefinition.CREATED],
                target=StatusDefinition.PLEDGED)
    def pledged(self):
        pass

    @transition(field=status,
                source=[StatusDefinition.LOCKED, StatusDefinition.FAILED],
                target=StatusDefinition.PENDING)
    def pending(self):
        self.confirmed = now()

    @transition(field=status,
                source=[StatusDefinition.PENDING, StatusDefinition.LOCKED,
                        StatusDefinition.FAILED],
                target=StatusDefinition.SUCCESS)
    def success(self):
        if not self.confirmed:
            self.confirmed = now()
        self.completed = now()

    @transition(field=status,
                source=[StatusDefinition.LOCKED, StatusDefinition.PENDING,
                        StatusDefinition.SUCCESS],
                target=StatusDefinition.FAILED)
    def failed(self):
        self.completed = None
        self.confirmed = None

    def update_total(self, save=True):
        donations = Donation.objects.filter(order=self, amount__gt=0).\
            values('amount_currency').annotate(Sum('amount')).order_by()

        total = [Money(data['amount__sum'], data['amount_currency']) for data in donations]
        if len(total) > 1:
            raise ValueError('Multiple currencies in one order')
        self.total = total[0]
        if save:
            self.save()

    def get_status_mapping(self, order_payment_status):
        return self.STATUS_MAPPING.get(order_payment_status,
                                       StatusDefinition.FAILED)

    def set_status(self, status, save=True):
        self.status = status
        if save:
            self.save()

    def __unicode__(self):
        return "{0} : {1}".format(self.id, self.created)

    def get_latest_order_payment(self):
        if self.order_payments.count():
            return self.order_payments.order_by('-created').all()[0]
        return None

    @property
    def order_payment(self):
        return self.get_latest_order_payment()

    class Meta:
        abstract = True
        permissions = (
            ('api_read_order', 'Can view order through the API'),
            ('api_add_order', 'Can add order through the API'),
            ('api_change_order', 'Can change order through the API'),
            ('api_delete_order', 'Can delete order through the API'),

            ('api_read_own_order', 'Can view own order through the API'),
            ('api_add_own_order', 'Can add own order through the API'),
            ('api_change_own_order', 'Can change own order through the API'),
            ('api_delete_own_order', 'Can delete own order through the API'),

        )


import signals  # noqa
