# coding=utf-8
from bluebottle.payments.adapters import BasePaymentAdapter

from .models import ExternalPayment


class ExternalPaymentAdapter(BasePaymentAdapter):
    MODEL_CLASSES = [ExternalPayment]

    card_data = {}

    def create_payment(self):
        """
        Create a new payment
        """
        payment = self.MODEL_CLASSES[0](order_payment=self.order_payment)
        payment.status = 'started'
        payment.save()
        payment.status = 'settled'
        payment.save()
        self.payment = payment
        return payment

    def check_payment_status(self):
        pass
