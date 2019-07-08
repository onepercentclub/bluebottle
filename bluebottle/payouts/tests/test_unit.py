from mock import patch
import os

from django.test.utils import override_settings

from bluebottle.funding_stripe.tests.factories import StripePaymentProviderFactory
from bluebottle.test.factory_models.payouts import StripePayoutAccountFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.utils import json2obj

MERCHANT_ACCOUNTS = [
    {
        'merchant': 'stripe',
        'currency': 'EUR',
        'secret_key': 'sk_test_secret_key',
        'webhook_secret': 'whsec_test_webhook_secret'
    }
]


@override_settings(MERCHANT_ACCOUNTS=MERCHANT_ACCOUNTS)
class StripePayoutAccountTestCase(BluebottleTestCase):

    def setUp(self):
        super(StripePayoutAccountTestCase, self).setUp()
        StripePaymentProviderFactory.create()
        self.init_projects()
        self.payout_account = StripePayoutAccountFactory.create(account_id='acct_0000000123')

    @patch('bluebottle.payouts.models.stripe.Account.retrieve')
    def test_check_status(self, stripe_retrieve):
        stripe_retrieve.return_value = json2obj(
            open(os.path.dirname(__file__) + '/data/stripe_account_verified.json').read()
        )
        self.assertEquals(self.payout_account.reviewed, False)
        self.payout_account.check_status()
        self.payout_account.refresh_from_db()
        self.assertEquals(self.payout_account.reviewed, True)

    @patch('bluebottle.payouts.models.stripe.Account.retrieve')
    def test_check_status_unverified(self, stripe_retrieve):
        stripe_retrieve.return_value = json2obj(
            open(os.path.dirname(__file__) + '/data/stripe_account_unverified.json').read()
        )
        self.assertEquals(self.payout_account.reviewed, False)
        self.payout_account.check_status()
        self.payout_account.refresh_from_db()
        self.assertEquals(self.payout_account.reviewed, False)

    @patch('bluebottle.payouts.models.stripe.Account.retrieve')
    def test_check_status_verified_missing_fields(self, stripe_retrieve):
        stripe_retrieve.return_value = json2obj(
            open(os.path.dirname(__file__) + '/data/stripe_account_verified_missing.json').read()
        )
        self.assertEquals(self.payout_account.reviewed, False)
        self.payout_account.check_status()
        self.payout_account.refresh_from_db()
        self.assertEquals(self.payout_account.reviewed, False)
