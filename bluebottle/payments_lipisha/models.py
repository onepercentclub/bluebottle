from decimal import Decimal

from django.db import models
from django.utils.translation import ugettext as _

from bluebottle.payments.models import Payment
from bluebottle.projects.models import ProjectAddOn


class LipishaPayment(Payment):

    reference = models.CharField(
        help_text="Transaction reference",
        null=True, blank=True,
        max_length=200)

    """
    Possible statuses:
    Requested
    Completed
    Cancelled
    Voided
    Acknowledged
    Authorized
    Settled
    Reversed
    """
    transaction_status = models.CharField(
        help_text="Lipisha transaction status",
        null=True, blank=True,
        max_length=200)

    """
    Possible types:
    Payment
    Withdrawal
    Fee
    Messaging
    Payout
    """
    transaction_type = models.CharField(
        help_text="Lipisha transaction type",
        null=True, blank=True,
        max_length=200)

    transaction_amount = models.CharField(
        help_text="Lipisha transaction reference",
        null=True, blank=True,
        max_length=200)

    transaction_currency = models.CharField(
        help_text="Lipisha transaction currency",
        null=True, blank=True,
        max_length=200)

    transaction_reference = models.CharField(
        help_text="Lipisha Transaction reference",
        null=True, blank=True,
        max_length=200)

    transaction_reversal_status = models.CharField(
        help_text="Lipisha transaction reversal status",
        null=True, blank=True,
        max_length=200)

    transaction_account_name = models.CharField(
        help_text="Lipisha transaction account name",
        null=True, blank=True,
        max_length=200)

    transaction_account_number = models.CharField(
        help_text="Lipisha transaction account number",
        null=True, blank=True,
        max_length=200)

    transaction_date = models.CharField(
        help_text="Lipisha transaction date",
        null=True, blank=True,
        max_length=200)

    transaction_email = models.CharField(
        help_text="Lipisha transaction email",
        null=True, blank=True,
        max_length=200)

    transaction_method = models.CharField(
        help_text="Lipisha transaction method",
        null=True, blank=True,
        max_length=200)

    transaction_mobile_number = models.CharField(
        help_text="Lipisha transaction mobile number",
        null=True, blank=True,
        max_length=200)

    transaction_name = models.CharField(
        help_text="Lipisha transaction name",
        null=True, blank=True,
        max_length=200)

    transaction_fee = models.TextField(
        help_text="Lipisha transaction fee object",
        null=True, blank=True
    )

    response = models.TextField(help_text=_('Response from Lipisha'), null=True, blank=True)
    update_response = models.TextField(help_text=_('Result from Lipisha (status update)'), null=True, blank=True)

    class Meta:
        ordering = ('-created', '-updated')
        verbose_name = "Lipisha Payment"
        verbose_name_plural = "Lipisha Payments"

    def get_method_name(self):
        """ Return the payment method name."""
        return 'lipisha'

    def get_fee(self):
        """
        a fee of 1.5% of the value of the transaction.
        """
        fee = round(self.order_payment.amount * Decimal(0.015), 2)
        return fee


class LipishaProject(ProjectAddOn):

    type = 'mpesa'
    serializer = 'bluebottle.payments_lipisha.serializers.BaseProjectAddOnSerializer'
    account_number = models.CharField(max_length=100, null=True, blank=True,
                                      help_text='Lipisha account number')

    @property
    def paybill_number(self):
        from bluebottle.payments_lipisha.adapters import LipishaPaymentInterface
        return LipishaPaymentInterface().credentials['business_number']

    def __unicode__(self):
        return "{} - {}".format(self.account_number, self.project.title)
