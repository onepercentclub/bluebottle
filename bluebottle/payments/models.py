from django.conf import settings
from django.db import models
from django.utils.text import Truncator
from django.utils.translation import ugettext as _
from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from djchoices import DjangoChoices, ChoiceItem

from django.contrib.auth import get_user_model
from polymorphic.polymorphic_model import PolymorphicModel

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
    order = models.ForeignKey(settings.ORDERS_ORDER_MODEL, related_name='payments')

    status = models.CharField(_("Status"), max_length=20, choices=PaymentStatuses.choices, default=PaymentStatuses.new, db_index=True)

    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))
    closed = models.DateTimeField(_("Closed"), blank=True, editable=False, null=True)

    amount = models.DecimalField(_("Amount"), max_digits=16, decimal_places=2)

    # Payment method used
    payment_method_id = models.CharField(max_length=20, default='', blank=True)
    payment_submethod_id = models.CharField(max_length=20, default='', blank=True)


class PaymentMetaData(PolymorphicModel):

    payment = models.ForeignKey('payments.Payment')
    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))

    class Meta:
        ordering = ('-created', '-updated')


class PaymentMethod(PolymorphicModel):

    profile = models.CharField(_("profile"), max_length=20)
    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))


class Transaction(PolymorphicModel):

    payment = models.ForeignKey('payments.Payment')
    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))

    class Meta:
        ordering = ('-created', '-updated')


class TransactionStatusChange(PolymorphicModel):

    payment = models.ForeignKey('payments.Payment')
    created = CreationDateTimeField(_("Created"))


class PaymentLogLevels(DjangoChoices):
    info = ChoiceItem('info', label=_("INFO"))
    warn = ChoiceItem('warn', label=_("WARN"))
    error = ChoiceItem('error', label=_("ERROR"))


# TODO: Add fields for: source file, source line number, source version, IP
class PaymentLogEntry(models.Model):
    message = models.CharField(max_length=400)
    level = models.CharField(max_length=15, choices=PaymentLogLevels.choices)
    timestamp = CreationDateTimeField()
    payment = models.ForeignKey(Payment, related_name='log_entries')

    class Meta:
        ordering = ('-timestamp',)
        verbose_name = _("Payment Log")
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return '{0} {1}'.format(self.get_level_display(), Truncator(self.message).words(6))

    def log_entry(self):
        return '[{0}]  {1: <5}  {2 <5}  {3}'.format(self.timestamp.strftime("%d/%b/%Y %H:%M:%S"),
                                                    self.get_type_display(), self.get_level_display(), self.message)
