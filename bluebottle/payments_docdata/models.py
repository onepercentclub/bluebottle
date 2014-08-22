from bluebottle.payments.models import Payment, Transaction
from django.utils.translation import ugettext as _
from django.db import models
from django_countries.fields import CountryField
from decimal import Decimal as D


class DocdataPayment(Payment):
    # FIXME: This model is copied from https://github.com/edoburu/django-oscar-docdata
    # We have to decide if we need all these fields and the way status choices

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

    payment_cluster_id = models.CharField(_("Payment cluster id"), max_length=200, default='', unique=True)
    payment_cluster_key = models.CharField(_("Payment cluster key"), max_length=200, default='', unique=True)

    status = models.CharField(_("Status"), max_length=50, choices=STATUS_CHOICES, default=STATUS_NEW)
    language = models.CharField(_("Language"), max_length=5, blank=True, default='en')

    ideal_issuer_id = models.CharField(_("Ideal Issuer ID"), max_length=100, default='')
    default_pm = models.CharField(_("Default Payment Method"), max_length=100, default='')

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


class DocdataTransaction(Transaction):
    """
    Docdata calls this: Payment
    The base model for a docdata payment. The model can be used for a web menu payment.
    """
    # Note: We're not using DjangoChoices here so that we can write unknown statuses if they are presented by DocData.
    status = models.CharField(_("status"), max_length=30, default='NEW')
    docdata_id = models.CharField(_("Docdata ID"), max_length=100, unique=True)

    # This is the payment method id from DocData (e.g. IDEAL, MASTERCARD, etc)
    payment_method = models.CharField(max_length=60, default='', blank=True)

    authorization_status = models.CharField(max_length=60, default='', blank=True)
    authorization_amount = models.IntegerField(_("Amount in cents"), null=True)
    authorization_currency = models.CharField(max_length=10, default='', blank=True)

    capture_status = models.CharField(max_length=60, default='', blank=True)
    capture_amount = models.IntegerField(_("Amount in cents"), null=True)
    capture_currency = models.CharField(max_length=10, default='', blank=True)

    def __unicode__(self):
        return self.payment_id


class DocDataDirectDebitTransaction(Transaction):
    account_name = models.CharField(max_length=35)  # max_length from DocData
    account_city = models.CharField(max_length=35)  # max_length from DocData
    iban = models.CharField(max_length=35)  # max_length from DocData
    bic = models.CharField(max_length=35)  # max_length from DocData

