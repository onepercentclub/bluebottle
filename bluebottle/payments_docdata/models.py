from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _

from bluebottle.payments.exception import PaymentException
from bluebottle.payments.models import Payment, Transaction


class AbstractDocdataPayment(Payment):
    """ Abstract Docdata  payment class."""

    class Meta(Payment.Meta):
        abstract = True
        ordering = ('-created', '-updated')

    merchant_order_id = models.CharField(_("Order ID"), max_length=100,
                                         default='')

    payment_cluster_id = models.CharField(_("Payment cluster id"),
                                          max_length=200, default='',
                                          unique=True)
    payment_cluster_key = models.CharField(_("Payment cluster key"),
                                           max_length=200, default='',
                                           unique=True)

    language = models.CharField(_("Language"), max_length=5, blank=True, default='en')

    ideal_issuer_id = models.CharField(_("Ideal Issuer ID"), max_length=100, default='')
    default_pm = models.CharField(_("Default Payment Method"), max_length=100)

    # Track sent information
    total_gross_amount = models.IntegerField(_("Total gross amount"))
    currency = models.CharField(_("Currency"), max_length=10)
    country = models.CharField(_("Country_code"), max_length=2, null=True, blank=True)

    # Track received information
    total_registered = models.IntegerField(_("Total registered"), default=0)
    total_shopper_pending = models.IntegerField(_("Total shopper pending"), default=0)
    total_acquirer_pending = models.IntegerField(_("Total acquirer pending"), default=0)
    total_acquirer_approved = models.IntegerField(_("Total acquirer approved"), default=0)
    total_captured = models.IntegerField(_("Total captured"), default=0)
    total_refunded = models.IntegerField(_("Total refunded"), default=0)
    total_charged_back = models.IntegerField(_("Total charged back"), default=0)

    # Track received information
    # Additional fields from the existing Docdata data. This data comes
    # from the existing DocDataPaymentOrder model that is migrated.
    customer_id = models.PositiveIntegerField(
        default=0)  # Defaults to 0 for anonymous.
    email = models.EmailField(max_length=254, default='')
    first_name = models.CharField(max_length=200, default='')
    last_name = models.CharField(max_length=200, default='')
    address = models.CharField(max_length=200, default='')
    postal_code = models.CharField(max_length=20, default='')
    city = models.CharField(max_length=200, default='')
    ip_address = models.CharField(max_length=200, default='')

    @property
    def transaction_reference(self):
        return self.merchant_order_id

    def get_method_name(self):
        """ Return the payment method name.

        In Docdata, this is the default_pm field.
        """
        return self.default_pm

    def get_fee(self):
        """ Return the fee that is withheld on this payment.

        This is depended on the payment method. Actual percentages are
        stored in the client properties
        """
        if not hasattr(settings, 'DOCDATA_FEES'):
            raise PaymentException("Missing fee DOCDATA_FEES")
        fees = settings.DOCDATA_FEES
        if not fees.get('transaction'):
            raise PaymentException("Missing fee 'transaction'")
        if not fees.get('payment_methods'):
            raise PaymentException("Missing fee 'payment_methods'")
        transaction_fee = fees['transaction']

        pm = self.default_pm.lower()

        try:
            pm_fee = fees['payment_methods'][pm]
        except KeyError:
            raise PaymentException("Missing fee {0}".format(pm))

        if '%' in str(pm_fee):
            part = Decimal(pm_fee.replace('%', '')) / 100
            return self.order_payment.amount.amount * part
        else:
            return pm_fee + transaction_fee


class DocdataPayment(AbstractDocdataPayment):
    """ Docdata Payment.

    This class is used to store all payments except direct debit.
    """

    class Meta(AbstractDocdataPayment.Meta):
        verbose_name = _("Docdata Payment")
        verbose_name_plural = _("Docdata Payments")


class DocdataDirectdebitPayment(AbstractDocdataPayment):
    """ Docdata direct debit class.

    Used to store all direct debit payments.
    """

    class Meta(AbstractDocdataPayment.Meta):
        verbose_name = _("Docdata Direct Debit Payment")
        verbose_name_plural = _("Docdata Direct Debit Payments")

    account_name = models.CharField(max_length=35)  # max_length from DocData
    account_city = models.CharField(max_length=35)  # max_length from DocData
    iban = models.CharField(max_length=35)  # max_length from DocData
    bic = models.CharField(max_length=35)  # max_length from DocData
    agree = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """Make sure the payment method is always direct debit.
        """
        if self.default_pm != 'sepa_direct_debit':
            self.default_pm = 'sepa_direct_debit'
        super(DocdataDirectdebitPayment, self).save(*args, **kwargs)


class DocdataTransaction(Transaction):
    """
    Docdata calls this: Payment
    The base model for a docdata payment. The model can be used for a web menu payment.
    """
    # Note: We're not using DjangoChoices here so that we can write unknown statuses if they are presented by DocData.
    status = models.CharField(_("status"), max_length=30, default='NEW')
    docdata_id = models.CharField(_("Docdata ID"), max_length=100, unique=False)

    # This is the payment method id from DocData (e.g. IDEAL, MASTERCARD, etc)
    payment_method = models.CharField(max_length=60, default='', blank=True)

    authorization_status = models.CharField(max_length=60, default='',
                                            blank=True)
    authorization_amount = models.IntegerField(_("Amount in cents"), null=True)
    authorization_currency = models.CharField(max_length=10, default='',
                                              blank=True)

    capture_status = models.CharField(max_length=60, default='', blank=True)
    capture_amount = models.IntegerField(_("Amount in cents"), null=True)
    chargeback_amount = models.IntegerField(_("Charge back amount in cents"),
                                            null=True)
    refund_amount = models.IntegerField(_("Refund amount in cents"), null=True)
    capture_currency = models.CharField(max_length=10, default='', null=True)
    raw_response = models.TextField(blank=True)

    def __unicode__(self):
        return unicode(self.id)
