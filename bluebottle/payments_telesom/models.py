from decimal import Decimal

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
        default="USD",
        null=True, blank=True,
        max_length=200)
    mobile = models.CharField(
        help_text="Mobile Number",
        null=True, blank=True,
        max_length=200)
    transaction_reference = models.CharField(
        help_text="Transaction reference for tracking transaction",
        null=True, blank=True,
        max_length=100)
    description = models.CharField(
        help_text="Description",
        null=True, blank=True,
        max_length=200)
    response = models.TextField(
        help_text=_('Response from Telesom'),
        null=True, blank=True)
    update_response = models.TextField(
        help_text=_('Result from Telesom (status update)'),
        null=True, blank=True)

    class Meta:
        ordering = ('-created', '-updated')
        verbose_name = "Telesom/Zaad Payment"
        verbose_name_plural = "Telesom/Zaad Payments"

    def get_method_name(self):
        """ Return the payment method name."""
        return 'telesom'

    def get_fee(self):
        """
        Not sure about the fee yet.
        """
        fee = round(self.order_payment.amount * Decimal(0.05), 2)
        return fee
