from decimal import Decimal
import json

from django.db import models
from django.utils.translation import ugettext as _

from bluebottle.payments.models import Payment


class TelesomPayment(Payment):

    amount = models.CharField(
        help_text="Amount",
        null=True, blank=True,
        max_length=200)
    currency = models.CharField(
        help_text="Transaction currency",
        default="NGN",
        null=True, blank=True,
        max_length=200)
    subscriber = models.CharField(
        help_text="Telesom valid mobile number of format 63XXXXXXX",
        null=True, blank=True,
        max_length=200)
    description = models.TextField(
        help_text="description about this transaction"
                  "",
        null=True, blank=True,
        max_length=200)

    response = models.TextField(help_text=_('Response from Telesom'), null=True, blank=True)
    update_response = models.TextField(help_text=_('Response from Telesom (status update)'), null=True, blank=True)

    class Meta:
        ordering = ('-created', '-updated')

    def get_method_name(self):
        """
        Return the payment method name.
        """
        return 'zaad'

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
            except (TypeError, KeyError):
                pass
        super(TelesomPayment, self).save(*args, **kwargs)
