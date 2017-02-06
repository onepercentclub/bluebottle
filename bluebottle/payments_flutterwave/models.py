from decimal import Decimal
import json

from django.db import models
from django.utils.translation import ugettext as _

from bluebottle.payments.models import Payment


class FlutterwavePayment(Payment):

    amount = models.CharField(
        help_text="Amount",
        null=True, blank=True,
        max_length=200)
    currency = models.CharField(
        help_text="Transaction currency",
        default="NGN",
        null=True, blank=True,
        max_length=200)
    auth_model = models.CharField(
        help_text="Authentication Model - BVN, PIN, NOAUTH, VBVSECURECODE",
        default="BVN",
        null=True, blank=True,
        max_length=200)
    card_number = models.CharField(
        help_text="Card Number",
        null=True, blank=True,
        max_length=200)
    cvv = models.CharField(
        help_text="Card CVV",
        null=True, blank=True,
        max_length=200)
    expiry_month = models.CharField(
        help_text="Card expiry month",
        null=True, blank=True,
        max_length=4)
    expiry_year = models.CharField(
        help_text="Card expiry year",
        null=True, blank=True,
        max_length=4)
    bvn = models.CharField(
        help_text="User BVN, required only for authModel=BVN",
        default='',
        null=True, blank=True,
        max_length=200)
    pin = models.CharField(
        help_text="User PIN, required only for authModel=PIN",
        default='',
        null=True, blank=True,
        max_length=200)
    customer_id = models.CharField(
        help_text="Customer ID for tracking charge transaction",
        null=True, blank=True,
        max_length=100)
    narration = models.CharField(
        help_text="Transaction description",
        null=True, blank=True,
        max_length=200)
    response_url = models.CharField(
        help_text="Callback Url",
        null=True, blank=True,
        max_length=200)
    country = models.CharField(
        help_text="Country code (NG)",
        default="NG",
        null=True, blank=True,
        max_length=200)

    transaction_reference = models.CharField(
        help_text="Flutterwave transaction reference",
        null=True, blank=True,
        max_length=200)

    response = models.CharField(help_text=_('Response from Flutterwave'),
                                max_length=1000, null=True, blank=True)
    update_response = models.CharField(help_text=_('Result from Flutterware (status update)'),
                                       max_length=1000, null=True, blank=True)

    class Meta:
        ordering = ('-created', '-updated')
        verbose_name = "Flutterwave Payment"
        verbose_name_plural = "Flutterwave Payments"

    def get_method_name(self):
        """ Return the payment method name."""
        return 'flutterwave'

    def get_fee(self):
        """
        a fee of 1.5% of the value of the transaction subject to a cap
        of N2,000 is charged. (i.e. for transactions below N133,333, a
        fee of 1.5% applies), and N2,000 flat fee (for transactions above N133,333).
        """
        fee = round(self.order_payment.amount * Decimal(0.015), 2)
        fee += 50
        if fee > 2000:
            return 2000
        return fee

    def save(self, *args, **kwargs):
        if not self.transaction_reference and self.response:
            try:
                self.transaction_reference = json.loads(self.response)['data']['transactionreference']
            except KeyError:
                pass
        super(FlutterwavePayment, self).save(*args, **kwargs)
