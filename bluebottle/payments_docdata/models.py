from decimal import Decimal as D, Decimal
from django.conf import settings
from django.utils.translation import ugettext as _
from django.db import models
from django.db.models.signals import pre_save, post_save, post_delete
from django_countries.fields import CountryField

from bluebottle.payments.exception import PaymentException
from bluebottle.payments.models import Payment, Transaction
from bluebottle.payments_logger.models import PaymentLogEntry


payment_method_icon_mapping = {
    'ideal': 'images/payments_docdata/icons/icon-ideal.svg',
    'direct_debit': 'images/payments_docdata/icons/icon-direct-debit.png',
    'sepa_direct_debit': 'images/payments_docdata/icons/icon-direct-debit.png',
    'mastercard': 'images/payments_docdata/icons/icon-mastercard.svg',
    'visa': 'images/payments_docdata/icons/icon-visa.svg',
    'system': 'images/payments_docdata/icons/icon-docdata.png'
}


class DocdataPayment(Payment):

    merchant_order_id = models.CharField(_("Order ID"), max_length=100, default='')

    payment_cluster_id = models.CharField(_("Payment cluster id"), max_length=200, default='', unique=True)
    payment_cluster_key = models.CharField(_("Payment cluster key"), max_length=200, default='', unique=True)

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
    total_charged_back = models.DecimalField(_("Total charged back"), max_digits=15, decimal_places=2, default=D('0.00'))

    # Additional fields from the existing Docdata data. This data comes from the existing DocDataPaymentOrder model that is migrated.
    customer_id = models.PositiveIntegerField(default=0)  # Defaults to 0 for anonymous.
    email = models.EmailField(max_length=254, default='')
    first_name = models.CharField(max_length=200, default='')
    last_name = models.CharField(max_length=200, default='')
    address = models.CharField(max_length=200, default='')
    postal_code = models.CharField(max_length=20, default='')
    city = models.CharField(max_length=200, default='')
    ip_address = models.CharField(max_length=200, default='')

    def get_method_name(self):
        return self.default_pm

    def get_method_icon(self):
        if self.get_method_name().lower() in payment_method_icon_mapping:
            return payment_method_icon_mapping[self.get_method_name().lower()]
        else:
            return payment_method_icon_mapping['system']

    def get_fee(self):
        if not hasattr(settings, 'DOCDATA_FEES'):
            raise PaymentException("Missing fee DOCDATA_FEES")
        fees = settings.DOCDATA_FEES
        if not fees.get('transaction', None):
            raise PaymentException("Missing fee 'transaction'")
        if not fees.get('payment_methods', None):
            raise PaymentException("Missing fee 'payment_methods'")
        transaction_fee = fees['transaction']

        pm = self.default_pm.lower()

        try:
            pm_fee = fees['payment_methods'][pm]
        except KeyError:
            raise PaymentException("Missing fee {0}".format(pm))

        if '%' in str(pm_fee):
            part = Decimal(pm_fee.replace('%', '')) / 100
            return self.order_payment.amount * part
        else:
            return pm_fee + transaction_fee

    class Meta:
        ordering = ('-created', '-updated')
        verbose_name = _("Docdata Payment")
        verbose_name_plural = _("Docdata Payments")


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

    authorization_status = models.CharField(max_length=60, default='', blank=True)
    authorization_amount = models.IntegerField(_("Amount in cents"), null=True)
    authorization_currency = models.CharField(max_length=10, default='', blank=True)

    capture_status = models.CharField(max_length=60, default='', blank=True)
    capture_amount = models.IntegerField(_("Amount in cents"), null=True)
    capture_currency = models.CharField(max_length=10, default='', blank=True)

    def __unicode__(self):
        return self.id


class DocdataDirectdebitPayment(Payment):

    merchant_order_id = models.CharField(_("Order ID"), max_length=100, default='')

    payment_cluster_id = models.CharField(_("Payment cluster id"), max_length=200, default='', unique=True)
    payment_cluster_key = models.CharField(_("Payment cluster key"), max_length=200, default='', unique=True)

    language = models.CharField(_("Language"), max_length=5, blank=True, default='en')

    ideal_issuer_id = models.CharField(_("Ideal Issuer ID"), max_length=100, default='')
    default_pm = models.CharField(_("Default Payment Method"), max_length=100, default='')

    # Track sent information
    total_gross_amount = models.IntegerField(_("Total gross amount"), help_text=_("Amount in cents"))
    currency = models.CharField(_("Currency"), max_length=10)
    country = models.CharField(_("Country_code"), max_length=2, null=True, blank=True)

    # Track received information
    total_registered = models.IntegerField(_("Total registered"), default=D('0.00'))
    total_shopper_pending = models.IntegerField(_("Total shopper pending"), default=D('0.00'))
    total_acquirer_pending = models.IntegerField(_("Total acquirer pending"), default=D('0.00'))
    total_acquirer_approved = models.IntegerField(_("Total acquirer approved"), default=D('0.00'))
    total_captured = models.IntegerField(_("Total captured"), default=D('0.00'))
    total_refunded = models.IntegerField(_("Total refunded"), default=D('0.00'))
    total_charged_back = models.IntegerField(_("Total charged back"), default=D('0.00'))

    class Meta:
        ordering = ('-created', '-updated')
        verbose_name = _("Docdata Direct Debit Payment")
        verbose_name_plural = _("Docdata Direct Debit Payments")

    account_name = models.CharField(max_length=35)  # max_length from DocData
    account_city = models.CharField(max_length=35)  # max_length from DocData
    iban = models.CharField(max_length=35)  # max_length from DocData
    bic = models.CharField(max_length=35)  # max_length from DocData
    agree = models.BooleanField(default=False)
