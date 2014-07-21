from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _
from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from djchoices import DjangoChoices, ChoiceItem

from django.contrib.auth import get_user_model

USER_MODEL = get_user_model()


class PaymentStatuses(DjangoChoices):
    new = ChoiceItem('new', label=_("New"))
    in_progress = ChoiceItem('in_progress', label=_("In Progress"))
    pending = ChoiceItem('pending', label=_("Pending"))
    paid = ChoiceItem('paid', label=_("Paid"))
    failed = ChoiceItem('failed', label=_("Failed"))
    cancelled = ChoiceItem('cancelled', label=_("Cancelled"))
    chargedback = ChoiceItem('chargedback', label=_("Chargedback"))
    refunded = ChoiceItem('refunded', label=_("Refunded"))
    unknown = ChoiceItem('unknown', label=_("Unknown"))  # Payments with this status have not been mapped.


class Payment(models.Model):
    """
    An order is a collection of OrderItems and vouchers with a connected payment.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("user"), blank=True, null=True)
    order = models.ForeignKey('orders.Order', related_name='payments')

    status = models.CharField(_("Status"), max_length=20, choices=PaymentStatuses.choices, default=PaymentStatuses.new, db_index=True)

    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))
    closed = models.DateTimeField(_("Closed"), blank=True, editable=False, null=True)

    amount = models.DecimalField(_("Amount"), max_digits=16, decimal_places=2)

    # Payment method used
    payment_method_id = models.CharField(max_length=20, default='', blank=True)
    payment_submethod_id = models.CharField(max_length=20, default='', blank=True)


class PaymentMetaData(models.Model):

    payment = models.ForeignKey('payments.Payment')

    class Meta:
        abstract = True


class PaymentMethod(models.Model):

    name = models.CharField(_("name"), max_length=20)

    class Meta:
        abstract = True

