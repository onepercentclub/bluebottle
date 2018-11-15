from django.contrib.postgres.fields.jsonb import JSONField
from django.db import models
from bluebottle.payments.models import Payment


class StripePayment(Payment):
    """
    Stripe payment class.
    """

    token = models.CharField(max_length=100, unique=True)
    data = JSONField(null=True)

    def get_fee(self):
        """
        Return the fee that is withheld on this payment.
        This is depended on the payment method.
        """
        return 0.0
