import json
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
        'pending': StatusDefinition.AUTHORIZED,  # TODO: Make sure this is correct!
        'failed': StatusDefinition.FAILED,

    }

    def __init__(self, order_payment):
        self.live_mode = getattr(properties, 'LIVE_PAYMENTS_ENABLED', False)
        self.order_payment = order_payment
        super(StripePaymentAdapter, self).__init__(order_payment)

    def _get_mapped_status(self, status):
        return self.status_mapping[status]

    def create_payment(self):
        chargeable = self.order_payment.card_data.pop('chargeable', False)
        self.payment = StripePayment(order_payment=self.order_payment, **self.order_payment.card_data)
        self.payment.save()

        if chargeable:
            self.charge()

        return self.payment

    def charge(self):
        if not self.payment.charge_token:

            account_id = self.order_payment.project.payout_account.account_id

            charge = stripe.Charge.create(
                amount=self.payment.amount,
                currency=self.payment.currency,
                description=self.payment.description,
                source=self.payment.source_token,
                destination={
                    "account": account_id,
                },
                api_key=self.credentials['secret_key']
            )
            self.payment.charge_token = charge.id
            self.update_from_charge(charge)

    def update_from_charge(self, charge):
        self.payment.data = json.loads(unicode(charge))
        self.payment.status = self._get_mapped_status(charge.status)

        if charge.refunded:
            self.payment.status = StatusDefinition.REFUNDED

        self.payment.save()

    def check_payment_status(self):
        if self.payment.charge_token:
            charge = stripe.Charge.retrieve(
                self.payment.charge_token,
                api_key=self.credentials['secret_key']
            )
            self.update_from_charge(charge)

    def refund_payment(self):
        stripe.Refund.create(
            charge=self.payment.charge_token,
            api_key=self.credentials['secret_key']
        )
        self.payment.status = StatusDefinition.REFUND_REQUESTED
        self.payment.save()

    def get_authorization_action(self):
        if not self.payment.charge_token:
            source = stripe.Source.retrieve(
                self.payment.source_token,
                api_key=self.credentials['secret_key']
            )
            # Check if we should redirect the user
            if source['flow'] == 'redirect':
                return {'type': 'redirect', 'method': 'get', 'url': source['redirect']['url']}
        return {
            'type': 'success'
        }
