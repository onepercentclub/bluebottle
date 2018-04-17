# coding=utf-8
import beyonic

from bluebottle.payments.exception import PaymentException
from django.db import connection

from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.utils.utils import get_current_host

from .models import BeyonicPayment


class BeyonicPaymentAdapter(BasePaymentAdapter):

    card_data = {}
    #  successful, failed, pending or cashed_out
    status_mapping = {
        'pending': 'started',
        'successful': 'settled',
        'failed': 'failed',
        'cashed_out': 'unknown'
    }

    def create_payment(self):
        """
        Create a new payment
        """
        self.card_data = self.order_payment.card_data

        if 'mobile' not in self.card_data:
            raise PaymentException('Mobile is required')

        mobile = self.card_data['mobile']
        if mobile[0:2] == '07':
            mobile = '+256' + mobile[1:]

        payment = BeyonicPayment(order_payment=self.order_payment,
                                 mobile=mobile)
        payment.amount = int(self.order_payment.amount.amount)
        payment.currency = str(self.order_payment.amount.currency)

        payment.metadata = {'order_id': self.order_payment.id}

        if not self.credentials['live']:
            # Testing currency
            payment.currency = 'BXC'

        tenant = connection.tenant
        payment.description = '{0}-{1}'.format(tenant.name, self.order_payment.id)

        beyonic.api_key = self.credentials['merchant_key']
        callback_url = '{0}/payments_beyonic/update/'.format(get_current_host())
        response = beyonic.CollectionRequest.create(
            phonenumber=payment.mobile,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            callback_url=callback_url,
            metadata=payment.metadata,
            send_instructions=True
        )

        payment.transaction_reference = response['id']
        payment.status = self.status_mapping[response['status']]
        payment.response = response
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
                    'method': 'beyonic-sms',
                    'text': 'Confirm the payment on your mobile'
                }
            }
        else:
            try:
                reply = self.payment.update_response['error_message']
            except KeyError:
                reply = self.payment.update_response
            raise PaymentException("Error processing AirTel/MTN transaction. {0}".format(reply))

    def check_payment_status(self):
        if self.payment.status == 'settled':
            return
        beyonic.api_key = self.credentials['merchant_key']
        response = beyonic.CollectionRequest.get(self.payment.transaction_reference)
        self.payment.update_response = response
        self.payment.status = self.status_mapping[response['status']]
        self.payment.save()

        if self.order_payment.authorization_action:
            self.order_payment.authorization_action.delete()

        action = self.get_authorization_action()
        if self.payment.status == 'settled':
            self.order_payment.settled()
        self.order_payment.set_authorization_action(action)
        self.order_payment.save()
