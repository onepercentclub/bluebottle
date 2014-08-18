from bluebottle.payments.models import Payment, Transaction
from django.utils.translation import ugettext as _
from django.db import models
from django_countries.fields import CountryField
from decimal import Decimal as D


class DocdataPayment(Payment):

    # Simplified internal status codes.
    # Lowercased on purpose to avoid mixing the statuses together.
    STATUS_NEW = 'new'                    # Initial state
    STATUS_IN_PROGRESS = 'in_progress'    # In the redirect phase
    STATUS_PENDING = 'pending'            # Waiting for user to complete payment (e.g. credit cards)
    STATUS_PAID = 'paid'                  # End of story, paid!
    STATUS_CANCELLED = 'cancelled'        # End of story, cancelled
    STATUS_CHARGED_BACK = 'charged_back'  # End of story, consumer asked for charge back
    STATUS_REFUNDED = 'refunded'          # End of story, refunded, merchant refunded
    STATUS_EXPIRED = 'expired'           # No results of customer, order was closed.
    STATUS_UNKNOWN = 'unknown'            # Help!

    STATUS_CHOICES = (
        (STATUS_NEW, _("New")),
        (STATUS_IN_PROGRESS, _("In Progress")),
        (STATUS_PENDING, _("Pending")),
        (STATUS_PAID, _("Paid")),
        (STATUS_CANCELLED, _("Cancelled")),
        (STATUS_CHARGED_BACK, _("Charged back")),
        (STATUS_REFUNDED, _("Refunded")),
        (STATUS_EXPIRED, _("Expired")),
        (STATUS_UNKNOWN, _("Unknown")),
    )

    merchant_order_id = models.CharField(_("Order ID"), max_length=100, default='')
    order_key = models.CharField(_("Payment cluster ID"), max_length=200, default='', unique=True)

    status = models.CharField(_("Status"), max_length=50, choices=STATUS_CHOICES, default=STATUS_NEW)
    language = models.CharField(_("Language"), max_length=5, blank=True, default='en')

    ideal_issuer_id = models.CharField(_("Ideal Issuer ID"), max_length=100, default='')

    # Track sent information
    total_gross_amount = models.DecimalField(_("Total gross amount"), max_digits=15, decimal_places=2)
    currency = models.CharField(_("Currency"), max_length=10)
    country = models.CharField(_("Country_code"), max_length=2, null=True, blank=True)

    # Track received information
    total_registered = models.DecimalField(_("Total registered"), max_digits=15, decimal_places=2, default=D('0.00'))
    total_shopper_pending = models.DecimalField(_("Total shopper pending"), max_digits=15, decimal_places=2, default=D('0.00'))
    total_acquirer_pending = models.DecimalField(_("Total acquirer pending"), max_digits=15, decimal_places=2, default=D('0.00'))
    total_acquirer_approved = models.DecimalField(_("Total acquirer approved"), max_digits=15, decimal_places=2, default=D('0.00'))
    total_captured = models.DecimalField(_("Total captured"), max_digits=15, decimal_places=2, default=D('0.00'))
    total_refunded = models.DecimalField(_("Total refunded"), max_digits=15, decimal_places=2, default=D('0.00'))
    total_charged_back = models.DecimalField(_("Total changed back"), max_digits=15, decimal_places=2, default=D('0.00'))

    class Meta:
        ordering = ('-created', '-updated')
        verbose_name = _("Docdata Order")
        verbose_name_plural = _("Docdata Orders")

    def __unicode__(self):
        return self.order_key

    @property
    def latest_payment(self):
        try:
            return self.payments.order_by('-merchant_order_id').all()[0]
        except IndexError:
            return None


class DocdataTransaction(Transaction):
    """
    Docdata calls this: Payment
    The base model for a docdata payment. The model can be used for a web menu payment.
    """
    # Note: We're not using DjangoChoices here so that we can write unknown statuses if they are presented by DocData.
    status = models.CharField(_("status"), max_length=30, default='NEW')
    payment_id = models.CharField(_("payment id"), max_length=100, default='', blank=True)

    # This is the payment method id from DocData (e.g. IDEAL, MASTERCARD, etc)
    payment_method = models.CharField(max_length=60, default='', blank=True)

    def __unicode__(self):
        return self.payment_id


class DocDataDirectDebitTransaction(Transaction):
    account_name = models.CharField(max_length=35)  # max_length from DocData
    account_city = models.CharField(max_length=35)  # max_length from DocData
    iban = models.CharField(max_length=35)  # max_length from DocData
    bic = models.CharField(max_length=35)  # max_length from DocData


############# Modeling from Oscar Docdata
# Osccar Dd  to Bluebottle Dd model renaming:
# DocdataOrder => DocdataPayment
# DocdataPayment => DocdataTransaction

#
# class DocdataOrder(models.Model):
#     """
#     Tracking of the order which is sent to docdata.
#     """
#     # Simplified internal status codes.
#     # Lowercased on purpose to avoid mixing the statuses together.
#     STATUS_NEW = 'new'                    # Initial state
#     STATUS_IN_PROGRESS = 'in_progress'    # In the redirect phase
#     STATUS_PENDING = 'pending'            # Waiting for user to complete payment (e.g. credit cards)
#     STATUS_PAID = 'paid'                  # End of story, paid!
#     STATUS_CANCELLED = 'cancelled'        # End of story, cancelled
#     STATUS_CHARGED_BACK = 'charged_back'  # End of story, consumer asked for charge back
#     STATUS_REFUNDED = 'refunded'          # End of story, refunded, merchant refunded
#     STATUS_EXPIRED = 'expired'           # No results of customer, order was closed.
#     STATUS_UNKNOWN = 'unknown'            # Help!
#
#     STATUS_CHOICES = (
#         (STATUS_NEW, _("New")),
#         (STATUS_IN_PROGRESS, _("In Progress")),
#         (STATUS_PENDING, _("Pending")),
#         (STATUS_PAID, _("Paid")),
#         (STATUS_CANCELLED, _("Cancelled")),
#         (STATUS_CHARGED_BACK, _("Charged back")),
#         (STATUS_REFUNDED, _("Refunded")),
#         (STATUS_EXPIRED, _("Expired")),
#         (STATUS_UNKNOWN, _("Unknown")),
#     )
#
#     merchant_order_id = models.CharField(_("Order ID"), max_length=100, default='')
#     order_key = models.CharField(_("Payment cluster ID"), max_length=200, default='', unique=True)
#
#     status = models.CharField(_("Status"), max_length=50, choices=STATUS_CHOICES, default=STATUS_NEW)
#     language = models.CharField(_("Language"), max_length=5, blank=True, default='en')
#
#     # Track sent information
#     total_gross_amount = models.DecimalField(_("Total gross amount"), max_digits=15, decimal_places=2)
#     currency = models.CharField(_("Currency"), max_length=10)
#     country = models.CharField(_("Country_code"), max_length=2, null=True, blank=True)
#
#     # Track received information
#     total_registered = models.DecimalField(_("Total registered"), max_digits=15, decimal_places=2, default=D('0.00'))
#     total_shopper_pending = models.DecimalField(_("Total shopper pending"), max_digits=15, decimal_places=2, default=D('0.00'))
#     total_acquirer_pending = models.DecimalField(_("Total acquirer pending"), max_digits=15, decimal_places=2, default=D('0.00'))
#     total_acquirer_approved = models.DecimalField(_("Total acquirer approved"), max_digits=15, decimal_places=2, default=D('0.00'))
#     total_captured = models.DecimalField(_("Total captured"), max_digits=15, decimal_places=2, default=D('0.00'))
#     total_refunded = models.DecimalField(_("Total refunded"), max_digits=15, decimal_places=2, default=D('0.00'))
#     total_charged_back = models.DecimalField(_("Total changed back"), max_digits=15, decimal_places=2, default=D('0.00'))
#
#     # Internal info.
#     created = models.DateTimeField(_("created"), auto_now_add=True)
#     updated = models.DateTimeField(_("updated"), auto_now=True)
#
#     class Meta:
#         ordering = ('-created', '-updated')
#         verbose_name = _("Docdata Order")
#         verbose_name_plural = _("Docdata Orders")
#
#     def __unicode__(self):
#         return self.order_key
#
#     @property
#     def latest_payment(self):
#         try:
#             return self.payments.order_by('-merchant_order_id').all()[0]
#         except IndexError:
#             return None
#
#     def cancel(self):
#         """
#         Cancel an order in Docdata.
#         """
#         from .facade import Facade
#         facade = Facade()
#         facade.cancel_order(self)
#
#     cancel.alters_data = True
#
#
# class DocdataPayment(PolymorphicModel):
#     """
#     A reported Docdata payment.
#     This is a summarized version of a Docdata payment transaction,
#     as returned by the status API call.
#
#     Some payment types have additional fields, which are stored as subclass.
#     """
#     docdata_order = models.ForeignKey(DocdataOrder, related_name='payments')
#     payment_id = models.CharField(_("Payment id"), max_length=100, default='', blank=True, primary_key=True)
#
#     # Note: We're not using choices here so that we can write unknown statuses if they are presented by Docdata.
#     status = models.CharField(_("status"), max_length=30, default='NEW')
#
#     # The payment method id from Docdata (e.g. IDEAL, MASTERCARD, etc)
#     payment_method = models.CharField(max_length=60, default='', blank=True)
#
#     # Track the various amounts associated with this source
#     confidence_level = models.CharField(_("Confidence level"), max_length=30, default='', editable=False)
#     amount_allocated = models.DecimalField(_("Amount Allocated"), decimal_places=2, max_digits=12, default=D('0.00'), editable=False)
#     amount_debited = models.DecimalField(_("Amount Debited"), decimal_places=2, max_digits=12, default=D('0.00'), editable=False)
#     amount_refunded = models.DecimalField(_("Amount Refunded"), decimal_places=2, max_digits=12, default=D('0.00'), editable=False)
#     amount_chargeback = models.DecimalField(_("Amount Changed back"), decimal_places=2, max_digits=12, default=D('0.00'), editable=False)
#
#     # Internal info.
#     created = models.DateTimeField(_("created"), auto_now_add=True)
#     updated = models.DateTimeField(_("updated"), auto_now=True)
#
#     def __unicode__(self):
#         return self.payment_id
#
#     class Meta:
#         ordering = ('payment_id',)
#         verbose_name = _("Payment")
#         verbose_name_plural = _("Payments")
