# coding=utf-8
import json

from bluebottle.payments.exception import PaymentException

from lipisha import Lipisha, lipisha

from bluebottle.clients import properties
from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.utils.utils import StatusDefinition

from .models import LipishaPayment


class LipishaPaymentAdapter(BasePaymentAdapter):

    card_data = {}

    STATUS_MAPPING = {
        'Requested': StatusDefinition.CREATED,
        'Completed': StatusDefinition.SETTLED,
        'Cancelled': StatusDefinition.CANCELLED,
        'Voided': StatusDefinition.FAILED,
        'Acknowledged': StatusDefinition.AUTHORIZED,
        'Authorized': StatusDefinition.AUTHORIZED,
        'Settled': StatusDefinition.SETTLED,
        'Reversed': StatusDefinition.REFUNDED
    }

    def __init__(self, order_payment):
        self.live_mode = getattr(properties, 'LIVE_PAYMENTS_ENABLED', False)
        if self.live_mode:
            env = lipisha.PRODUCTION_ENV
        else:
            env = lipisha.SANDBOX_ENV
        super(LipishaPaymentAdapter, self).__init__(order_payment)
        self.client = Lipisha(
            self.credentials['api_key'],
            self.credentials['api_signature'],
            api_environment=env
        )

    def _get_mapped_status(self, status):
        return self.STATUS_MAPPING[status]

    def _get_payment_reference(self):
        return "{}#{}".format(
            self.credentials['account_number'],
            self.payment.reference
        )

    def create_payment(self):
        payment = LipishaPayment(
            order_payment=self.order_payment,
        )
        payment.reference = self.order_payment.id
        payment.save()
        self.payment_logger.log(payment,
                                'info',
                                'payment_tracer: {}, '
                                'event: payment.lipisha.create_payment.success'.format(self.payment_tracer))

        self.payment = payment
        return payment

    def get_authorization_action(self):

        if self.payment.status == 'started':
            return {
                'type': 'process',
                'payload': {
                    'business_number': self.credentials['business_number'],
                    'account_number': self._get_payment_reference(),
                    'amount': int(float(self.order_payment.amount))
                }
            }
        else:
            self.check_payment_status()
            if self.payment.status in ['settled', 'authorized']:
                return {
                    'type': 'success'
                }
            else:
                return {
                    'type': 'pending'
                }

    def check_payment_status(self):

        response = self.client.get_transactions(
            transaction_type='Payment',
            transaction_reference=self.payment.reference
        )

        self.payment.response = json.dumps(response)
        data = response['content']

        if len(data) > 1:
            raise PaymentException('Payment could not be verified yet. Multiple payments found.')
        if len(data) == 0:
            raise PaymentException('Payment could not be verified yet. Payment not found.')
        else:
            payment = data[0]
            for k, v in payment.iteritems():
                setattr(self.payment, k, v)

        self.payment.status = self._get_mapped_status(self.payment.transaction_status)

        if self.payment.status in ['settled', 'authorized']:
            self.order_payment.set_authorization_action({'type': 'success'})

        self.payment.save()
