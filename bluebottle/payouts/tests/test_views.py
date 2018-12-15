from mock import patch

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from bluebottle.test.factory_models.payouts import StripePayoutAccountFactory
from bluebottle.test.utils import BluebottleTestCase


MERCHANT_ACCOUNTS = [
    {
        'merchant': 'stripe',
        'currency': 'EUR',
        'secret_key': 'sk_test_secret_key',
        'webhook_secret': 'whsec_test_webhook_secret'
    }
]


@override_settings(MERCHANT_ACCOUNTS=MERCHANT_ACCOUNTS)
class StripePayoutAccountUpdateTestCase(BluebottleTestCase):
    def setUp(self):
        self.payout_account = StripePayoutAccountFactory.create(
            account_id='acct_00000000000035'
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

    def test_update_account(self):
        """
        Test Stripe payout account update
        """
        with patch(
            'stripe.Webhook.construct_event',
            return_value=self.MockEvent(
                'account.updated', {'id': self.payout_account.account_id}
            )
        ):
            with patch(
                'bluebottle.payouts.models.StripePayoutAccount.check_status'
            ) as check_status:
                response = self.client.post(
                    reverse('stripe-webhook'),
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, 200)
                check_status.assert_called_once()
