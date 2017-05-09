import json
from decimal import Decimal

from django.db import models
from django.utils.translation import ugettext as _
from django_extensions.db.fields import CreationDateTimeField

from bluebottle.payments.models import Payment


class InterswitchPayment(Payment):
    product_id = models.CharField(help_text=_('Product Identifier for PAYDirect.'),
                                  max_length=200, null=True, blank=True)
    amount = models.CharField(help_text=_('Transaction amount in small (kobo or cents)'),
                              max_length=200, null=True, blank=True)
    currency = models.CharField(help_text=_('566 (For Naira)'), max_length=200, default='566')
    site_redirect_url = models.CharField(help_text=_('URL the user is to be redirected to after payment.'),
                                         max_length=200, null=True, blank=True)
    txn_ref = models.CharField(help_text=_('Transaction Reference Number.'),
                               max_length=200, null=True, blank=True)
    hash = models.CharField(help_text=_('A Hashed value of selected combined parameters.'),
                            max_length=200, null=True, blank=True)
    pay_item_id = models.CharField(help_text=_('PAYDirect Payment Item ID'),
                                   max_length=200, null=True, blank=True)
    site_name = models.CharField(help_text=_('Internet site name of the web site'),
                                 max_length=200, null=True, blank=True)
    cust_id = models.CharField(help_text=_('Unique Customer Identification Number'),
                               max_length=200, null=True, blank=True)
    cust_id_desc = models.CharField(help_text=_('Customer Identification Number description.'),
                                    max_length=200, null=True, blank=True)
    cust_name = models.CharField(help_text=_('Customer Name'), max_length=200, null=True, blank=True)
    cust_name_desc = models.CharField(help_text=_('Customer Name Description.'),
                                      max_length=200, null=True, blank=True)
    pay_item_name = models.CharField(help_text=_('PAYDirect Payment Item Name'),
                                     max_length=200, null=True, blank=True)
    local_date_time = models.CharField(help_text=_('Local Transaction Date time'),
                                       max_length=200, null=True, blank=True)
    response = models.CharField(help_text=_('Response from Interswitch'),
                                max_length=1000, null=True, blank=True)
    update_response = models.CharField(help_text=_('Result from Interswitch (status update)'),
                                       max_length=1000, null=True, blank=True)

    class Meta:
        ordering = ('-created', '-updated')
        verbose_name = "Interswitch Payment"
        verbose_name_plural = "Interswitch Payments"

    @property
    def transaction_reference(self):
        return self.txn_ref

    def get_method_name(self):
        """ Return the payment method name."""
        return 'interswitch'

    def get_fee(self):
        """
        a fee of 1.5% of the value of the transaction subject to a cap
        of N2,000 is charged. (i.e. for transactions below N133,333, a
        fee of 1.5% applies), and N2,000 flat fee (for transactions above N133,333).
        """
        fee = round(self.order_payment.amount * Decimal(0.015), 2)
        if fee > 2000:
            return 2000
        return fee

    @property
    def status_code(self):
        try:
            return json.loads(self.response)['ResponseCode']
        except (TypeError, KeyError):
            return ""

    @property
    def status_description(self):
        try:
            return json.loads(self.response)['ResponseDescription']
        except (TypeError, KeyError):
            return ""


class InterswitchPaymentStatusUpdate(models.Model):
    payment = models.ForeignKey('payments_interswitch.InterswitchPayment')
    created = CreationDateTimeField()
    result = models.TextField()
