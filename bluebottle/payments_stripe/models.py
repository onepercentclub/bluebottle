from django.db import models
from bluebottle.payments.models import Payment
from django.utils.translation import ugettext_lazy as _


class StripePayment(Payment):
    """
    Stripe payment class.
    """

    source_token = models.CharField(max_length=100, null=True, help_text=_("Source token obtained in front-end."))
    charge_token = models.CharField(max_length=100, null=True, help_text=_("Charge token at Stripe."))
    amount = models.IntegerField(null=True, help_text=_("Payment amount in smallest units (e.g. cents)."))
    currency = models.CharField(max_length=3, default='EUR')
    description = models.CharField(max_length=300, null=True)

    data = models.TextField(null=True)

    def get_fee(self):
        """
        Return the fee that is withheld on this payment.
        This is depended on the payment method.
        """
        return 0.0

    def save(self, *args, **kwargs):
        if not self.amount:
            self.amount = int(self.order_payment.amount.amount * 100)
            self.currency = self.order_payment.amount.currency
        if not self.description:
            self.description = "{} - {}".format(self.order_payment.id, self.order_payment.info_text)
        super(StripePayment, self).save(*args, **kwargs)
