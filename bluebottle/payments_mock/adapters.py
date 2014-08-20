# coding=utf-8
from bluebottle.payments.adapters import AbstractPaymentAdapter
from .models import MockPayment


class MockPaymentAdapter(AbstractPaymentAdapter):

    @staticmethod
    def create_payment(self, order_payment, meta_data=None, **kwargs):
        payment = MockPayment(**meta_data)
        return payment

    @staticmethod
    def get_authorization_action(self, order_payment):
        return {}


