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
        self.card_data = self.order_payment.card_data

        if 'mobile' not in self.card_data:
            raise PaymentException('Mobile is required')

        payment = self.MODEL_CLASSES[0](order_payment=self.order_payment,
                                        mobile=self.card_data['mobile'])
        payment.amount = int(self.order_payment.amount.amount)
        if str(self.order_payment.amount.currency) != 'USD':
            raise PaymentException('You should pick USD as a currency to use Telesom/Zaad')

        payment.currency = str(self.order_payment.amount.currency)
        payment.narration = "Donation {0}".format(self.order_payment.id)

        gateway = TelesomClient(
            merchant_id=self.credentials['merchant_id'],
            merchant_key=self.credentials['merchant_key'],
            username=self.credentials['username'],
            password=self.credentials['password'],
            api_domain=self.credentials['api_domain']
        )
        tenant = connection.tenant
        payment.description = '{0}-{1}'.format(tenant.name, self.order_payment.id)

        response = gateway.create(
            mobile=payment.mobile,
            amount=payment.amount,
            description=payment.description
        )
        payment.transaction_reference = response['payment_id']
        payment.status = response['status']
        payment.response = response['response']
        payment.save()

        self.payment = payment
        # Check status right away so the payment gets processed
        self.check_payment_status()
        return payment

    def get_authorization_action(self):
        """
        Handle payment
        """

        if self.payment.status == 'settled':
            return {'type': 'success'}
        elif self.payment.status == 'started':
            return {
                'type': 'step2',
                'payload': {
                    'method': 'telesom-sms',
                    'text': 'Confirm the payment by SMS'
                }
            }
        else:
            reply = self.payment.update_response
            raise PaymentException("Error processing Telesom/Zaad transaction. {0}".format(reply))

    def check_payment_status(self):
        if self.payment.status == 'settled':
            return
        gateway = TelesomClient(
            merchant_id=self.credentials['merchant_id'],
            merchant_key=self.credentials['merchant_key'],
            username=self.credentials['username'],
            password=self.credentials['password'],
            api_domain=self.credentials['api_domain']
        )
        response = gateway.check_status(self.payment.transaction_reference)

        status = response['status']

        # To properly test the live flow against the testing server we have to make sure
        # the payment doesn't get 'settled' on the first check. There for set it 'started'
        # first so the user has to confirm again after which it wil get 'settled'
        if self.payment.status == 'started' and status == 'settled':
            self.payment.status = 'settled'
            self.payment.update_response = response['response']
            self.payment.save()
        elif self.payment.status == 'created' and status == 'settled':
            self.payment.status = 'started'
            self.payment.update_response = response['response']
            self.payment.save()
        else:
            self.payment.status = 'started'
            self.payment.save()

        if self.order_payment.authorization_action:
            self.order_payment.authorization_action.delete()

        action = self.get_authorization_action()
        self.order_payment.set_authorization_action(action)
        self.order_payment.save()
