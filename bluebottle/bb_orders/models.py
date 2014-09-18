from bluebottle.utils.model_dispatcher import get_donation_model
from django.conf import settings
from django.db import models
from django.db.models.aggregates import Sum
from django.utils.translation import ugettext as _
from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from django.db.models import options
from django_fsm.db.fields import FSMField, transition

from bluebottle.utils.utils import FSMTransition, StatusDefinition

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('default_serializer', 'preview_serializer', 'manage_serializer')


class BaseOrder(models.Model, FSMTransition):
    """
    An Order is a collection of Donations with one or more OrderPayments referring to it.
    """
    # Mapping the Order Payment Status to the Order Status
    STATUS_MAPPING = {
        StatusDefinition.CREATED:      StatusDefinition.LOCKED,
        StatusDefinition.STARTED:      StatusDefinition.LOCKED,
        StatusDefinition.AUTHORIZED:   StatusDefinition.SUCCESS,
        StatusDefinition.SETTLED:      StatusDefinition.SUCCESS,
        StatusDefinition.CHARGED_BACK: StatusDefinition.FAILED,
        StatusDefinition.REFUNDED:     StatusDefinition.FAILED,
        StatusDefinition.FAILED:       StatusDefinition.FAILED,
        StatusDefinition.UNKNOWN:      StatusDefinition.FAILED
    }

    STATUS_CHOICES = (
        (StatusDefinition.CREATED, _('Created')),
        (StatusDefinition.LOCKED, _('Locked')),
        (StatusDefinition.SUCCESS, _('Success')),
        (StatusDefinition.FAILED, _('Failed')),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("user"), blank=True, null=True)
    status = FSMField(default=StatusDefinition.CREATED, choices=STATUS_CHOICES, protected=True)

    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))
    closed = models.DateTimeField(_("Closed"), blank=True, editable=False, null=True)

    total = models.DecimalField(_("Amount"), max_digits=16, decimal_places=2, default=0)

    @transition(field=status, save=True, source=StatusDefinition.CREATED, target=StatusDefinition.LOCKED)
    def locked(self):
        # TODO: add locked state behaviour here
        pass

    @transition(field=status, save=True, source=StatusDefinition.LOCKED, target=StatusDefinition.SUCCESS)
    def succeeded(self):
        # TODO: add success state behaviour here
        pass

    @transition(field=status, save=True, source=[StatusDefinition.LOCKED, StatusDefinition.SUCCESS], target=StatusDefinition.FAILED)
    def failed(self):
        # TODO: add failed state behaviour here
        pass

    def update_total(self, save=True):
        DONATION_MODEL = get_donation_model()
        donations = DONATION_MODEL.objects.filter(order=self)
        self.total = donations.aggregate(Sum('amount'))['amount__sum']
        if save:
            self.save()

    def get_status_mapping(self, order_payment_status):
        return self.STATUS_MAPPING.get(order_payment_status, StatusDefinition.FAILED)

    def set_status(self, status, save=True):
        self.status = status
        if save:
            self.save()

    def __unicode__(self):
        return "{0} : {1}".format(self.id, self.created)

    class Meta:
        abstract = True
        default_serializer = 'bluebottle.bb_orders.serializers.OrderSerializer'
        preview_serializer = 'bluebottle.bb_orders.serializers.OrderSerializer'
        manage_serializer = 'bluebottle.bb_orders.serializers.ManageOrderSerializer'

import signals
