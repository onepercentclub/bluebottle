from decimal import Decimal

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import ugettext_lazy as _

from bluebottle.payments.models import Payment


class BeyonicPayment(Payment):

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
    description = models.CharField(
        help_text="Description",
        null=True, blank=True,
        max_length=200)
    metadata = JSONField(
        help_text="Metadata",
        null=True, blank=True)
    transaction_reference = models.CharField(
        help_text="Transaction ID",
        null=True, blank=True,
        max_length=200)

    response = models.TextField(
        help_text=_('Response from Beyonic'),
        null=True, blank=True)
    update_response = models.TextField(
        help_text=_('Result from Beyonic (status update)'),
        null=True, blank=True)

    class Meta:
        ordering = ('-created', '-updated')
        verbose_name = "Beyonic Payment"
        verbose_name_plural = "Beyonic Payments"

    def get_method_name(self):
        """ Return the payment method name."""
        return 'beyonic'

    def get_fee(self):
        """
        Not sure about the fee yet.
        """
        fee = round(self.order_payment.amount * Decimal(0.05), 2)
        return fee
