from decimal import Decimal
from django.db import models
from djchoices import DjangoChoices, ChoiceItem
from django.utils.translation import gettext as _
from bluebottle.payments.models import Payment


class MockPayment(Payment):
    pass

    class Meta:
        ordering = ('-created', '-updated')
        verbose_name = "Mock Payment"
        verbose_name_plural = "Mock Payments"

    def get_fee(self):

        if self.order_payment.payment_method == 'mockIdeal':
            # Return a flat fee of 0.75 euro
            return Decimal(0.75)

        if self.order_payment.payment_method == 'mockCard':
            # Return 3.25% of amount
            return round(self.order_payment.amount * Decimal(0.0325), 2)

        else:
            # Return a flat fee of 0.75 euro
            return Decimal(0.75)
