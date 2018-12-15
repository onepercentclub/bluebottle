from mock import patch
import stripe

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.factory_models.payments_stripe import StripePaymentFactory
from bluebottle.test.utils import BluebottleTestCase


class MockEvent(object):
    def __init__(self, type):
        self.type = type


MERCHANT_ACCOUNTS = [
    {
        'merchant': 'stripe',
        'currency': 'EUR',
        'secret_key': 'sk_test_secret_key',
        'webhook_secret': 'whsec_test_webhook_secret'
    }
]

PAYMENT_METHODS = (
    {
        'provider': 'stripe',
        'id': 'stripe-creditcard',
        'profile': 'creditcard',
        'name': 'CreditCard',
        'currencies': {'EUR': {'min_amount': 5, 'max_amount': 1000}}
    },
)

@override_settings(
    MERCHANT_ACCOUNTS=MERCHANT_ACCOUNTS,
    PAYMENT_METHODS=PAYMENT_METHODS
)
class StripePaymentAdapterTestCase(BluebottleTestCase):
    def setUp(self):
        charge_token = 'charge_token'
        source_token = 'source_token'

        order_payment = OrderPaymentFactory.create(
            payment_method='stripe',
            amount=100
        )
        self.payment = StripePaymentFactory.create(
            charge_token=charge_token,
            source_token=source_token,
            order_payment=order_payment
        )

        class MockEvent(object):
            def __init__(self, type, object):
                self.type = type

                for key, value in object.items():
                    setattr(self.data.object, key, value)

            class data:
                class object:
                    pass

        self.MockEvent = MockEvent

    def test_charge_success(self):
        """
        Test Stripe payment webhook
        """
        with patch(
            'stripe.Webhook.construct_event',
            return_value=self.MockEvent(
                'charge.succeeded', {'id': self.payment.charge_token}
            )
        ):
            with patch(
                'bluebottle.payments_stripe.adapters.StripePaymentAdapter.update_from_charge'
            ) as update_from_charge:
                response = self.client.post(
                    reverse('stripe-webhook'),
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, 200)
                update_from_charge.assert_called_once()

    def test_source_chargeable(self):
        """
        Test Flutterwave payment that turns to success without otp (one time pin)
        """
        with patch(
            'stripe.Webhook.construct_event',
            return_value=self.MockEvent(
                'source.chargeable', {'id': self.payment.source_token}
            )
        ):
            with patch(
                'bluebottle.payments_stripe.adapters.StripePaymentAdapter.charge'
            ) as charge:
                response = self.client.post(
                    reverse('stripe-webhook'),
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                charge.assert_called_once()
                self.assertEqual(response.status_code, 200)

    def test_payment_does_not_exist(self):
        """
        Test Flutterwave payment that turns to success without otp (one time pin)
        """
        with patch(
            'stripe.Webhook.construct_event',
            return_value=self.MockEvent(
                'source.chargeable', {'id': 'does-not-exist'}
            )
        ):
            response = self.client.post(
                reverse('stripe-webhook'),
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, 400)

    def test_invalid_signature(self):
        """
        Test Flutterwave payment that turns to success without otp (one time pin)
        """
        with patch(
            'stripe.Webhook.construct_event',
            side_effect=stripe.error.SignatureVerificationError('Some Message', None)
        ):
            response = self.client.post(
                reverse('stripe-webhook'),
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, 400)
