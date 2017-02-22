# coding=utf-8
from bluebottle.payments.exception import PaymentException
from django.db import connection

from bluebottle.payments.adapters import BasePaymentAdapter

from .gateway import TelesomClient
from .models import TelesomPayment


class TelesomPaymentAdapter(BasePaymentAdapter):
    MODEL_CLASSES = [TelesomPayment]

    card_data = {}

    def create_payment(self):
        """
        Create a new payment
        """

        if 'mobile' not in self.card_data:
            raise PaymentException('Mobile is required')

        payment = self.MODEL_CLASSES[0](order_payment=self.order_payment,
                                        mobile=self.card_data['mobile'])
        payment.amount = str(self.order_payment.amount.amount)
        if str(self.order_payment.amount.currency) != 'USD':
            raise PaymentException('You should pick USD as a currency to use Telesom/Zaad')

        payment.currency = str(self.order_payment.amount.currency)
        payment.narration = "Donation {0}".format(self.order_payment.id)

        gateway = TelesomClient(
            merchant_id=self.credentials['merchant_id'],
            merchant_key=self.credentials['merchant_key'],
            username=self.credentials['username'],
            password=self.credentials['password'],
            api_url=self.credentials['api_url']
        )
        tenant = connection.tenant
        payment.description = '{0}-{1}'.format(tenant.name, self.order_payment.id)

        transaction_reference = gateway.create(
            mobile=payment.mobile,
            amount=payment.amount,
            description=payment.description
        )
        payment.transaction_reference = transaction_reference
        payment.save()
        return payment

    def get_authorization_action(self):
        """
        Handle payment
        """
        return {'type': 'success'}

    def check_payment_status(self):
        pass
