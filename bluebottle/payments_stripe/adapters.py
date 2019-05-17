import json
import logging
from decimal import Decimal

import stripe
from django.db import connection
from moneyed import Money
from stripe.error import StripeError

from bluebottle.clients import properties
from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.payments.exception import PaymentException
from bluebottle.payments_stripe.models import StripePayment

from bluebottle.utils.utils import StatusDefinition

logger = logging.getLogger(__name__)


class StripePaymentAdapter(BasePaymentAdapter):

    MODEL_CLASSES = [StripePayment]

    status_mapping = {
        'succeeded': StatusDefinition.SETTLED,
        'pending': StatusDefinition.AUTHORIZED,
        'failed': StatusDefinition.FAILED,
        'canceled': StatusDefinition.CANCELLED,
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
            tenant = connection.tenant

            try:
                charge = stripe.Charge.create(
                    amount=self.payment.amount,
                    currency=self.payment.currency,
                    description=self.payment.description,
                    source=self.payment.source_token,
                    destination={
                        "account": account_id,
                    },
                    metadata={
                        "tenant_name": tenant.client_name,
                        "tenant_domain": tenant.domain_url,
                        "project_slug": self.order_payment.project.slug,
                        "project_title": self.order_payment.project.title,
                    },
                    api_key=self.credentials['secret_key']
                )

                self.payment.charge_token = charge.id
                self.payment.save()

                if 'transfer' in charge:
                    transfer = stripe.Transfer.retrieve(
                        charge['transfer'],
                        api_key=self.credentials['secret_key']
                    )

                    self.update_from_transfer(transfer)
                self.update_from_charge(charge)
            except (stripe.error.CardError, stripe.error.InvalidRequestError) as e:
                self.payment.status = StatusDefinition.FAILED
                self.payment.save()
                raise PaymentException(e.message)
            except StripeError as e:
                raise PaymentException(e.message)

    def update_from_charge(self, charge):
        self.payment.data = json.loads(unicode(charge))
        self.payment.status = self._get_mapped_status(charge.status)

        if 'dispute' in charge and charge.dispute:
            dispute = stripe.Dispute.retrieve(
                charge.dispute,
                api_key=self.credentials['secret_key']
            )
            if dispute.status == 'lost':
                self.payment.status = StatusDefinition.CHARGED_BACK

        if charge.refunded:
            self.payment.status = StatusDefinition.REFUNDED

        self.payment.save()

    def update_from_transfer(self, transfer):
        self.payment.payout_amount = transfer['amount']
        self.payment.payout_amount_currency = transfer['currency']
        self.payment.save()

        # Set payout_amount on donation
        amount = Money(Decimal(transfer['amount']) / 100, transfer['currency'])
        donation = self.payment.order_payment.order.donations.first()
        donation.payout_amount = amount
        donation.save()

        self.payment.save()

    def update_from_source(self, source):
        if source.status in ('canceled', 'failed'):
            self.payment.status = self.status_mapping[source.status]
            self.payment.save()

        if not self.payment.charge_token and source.get('consumed'):
            self.payment.status = StatusDefinition.FAILED
            self.payment.save()

    def check_payment_status(self):
        if self.payment.charge_token:
            charge = stripe.Charge.retrieve(
                self.payment.charge_token,
                api_key=self.credentials['secret_key']
            )
            self.update_from_charge(charge)

            if 'transfer' in charge:
                transfer = stripe.Transfer.retrieve(
                    charge['transfer'],
                    api_key=self.credentials['secret_key']
                )
                self.update_from_transfer(transfer)
        else:
            source = stripe.Source.retrieve(
                self.payment.source_token,
                api_key=self.credentials['secret_key']
            )
            self.update_from_source(source)

    def refund_payment(self):
        stripe.Refund.create(
            charge=self.payment.charge_token,
            reverse_transfer=True,
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
        if self.payment.status == 'failed':
            raise PaymentException("Payment failed")
        return {
            'type': 'success'
        }
