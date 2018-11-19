import logging

import stripe

from bluebottle.clients import properties
from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.payments_stripe.models import StripePayment

from bluebottle.utils.utils import StatusDefinition

logger = logging.getLogger(__name__)


class StripePaymentAdapter(BasePaymentAdapter):

    status_mapping = {
        'succeeded': StatusDefinition.SETTLED,

    }

    def __init__(self, order_payment):
        self.live_mode = getattr(properties, 'LIVE_PAYMENTS_ENABLED', False)
        self.order_payment = order_payment
        stripe.api_key = self.credentials['secret_key']
        super(StripePaymentAdapter, self).__init__(order_payment)

    def _get_mapped_status(self, status):
        return self.status_mapping[status]

    def create_payment(self):
        payment = StripePayment(order_payment=self.order_payment, **self.order_payment.card_data)
        payment.save()

        charge = stripe.Charge.create(
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            source=payment.source_token
        )

        payment.status = self._get_mapped_status(charge['status'])
        payment.charge = charge.id
        payment.data = charge
        payment.save()

        return payment

    def check_payment_status(self):
        pass

    def refund_payment(self):
        pass

    def get_authorization_action(self):
        source = stripe.Source.retrieve(self.payment.source_token)
        if self.payment.status == StatusDefinition.SETTLED:
            return {
                'type': 'success'
            }

        # Check if we should redirect the user
        if source['flow'] == 'redirect':
            return {'type': 'redirect', 'method': 'get', 'url': source['redirect']['url']}
