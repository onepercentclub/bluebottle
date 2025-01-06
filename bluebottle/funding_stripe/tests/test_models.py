import munch
import mock
import stripe
from django.test.utils import override_settings

from bluebottle.funding_stripe.models import (
    StripePayoutAccount, ExternalAccount
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
)
class ConnectAccountTestCase(BluebottleTestCase):
    def setUp(self):
        account_id = 'some-connect-id'
        self.check = StripePayoutAccount(owner=BlueBottleUserFactory.create(), country='NL', account_id=account_id)

        self.connect_account = stripe.Account(account_id)
        self.connect_account.update(
            {
                "country": self.check.country,
                "charges_enabled": True,
                "payouts_enabled": True,
                "individual": munch.munchify(
                    {
                        "first_name": "Jhon",
                        "last_name": "Example",
                        "email": "jhon@example.com",
                        "requirements": munch.munchify(
                            {
                                "eventually_due": [
                                    "external_accounts",
                                    "individual.verification.document",
                                    "document_type",
                                ]
                            }
                        ),
                        "verification": munch.munchify({"status": "verified"}),
                    }
                ),
                "requirements": munch.munchify(
                    {
                        "eventually_due": [
                            "external_accounts",
                            "individual.verification.document.front",
                            "document_type",
                        ],
                        "disabled": False,
                    }
                ),
                "external_accounts": munch.munchify({"total_count": 0, "data": []}),
            }
        )

        self.country_spec = stripe.CountrySpec(self.check.country)
        self.country_spec.update({
            'verification_fields': munch.munchify({
                'individual': munch.munchify({
                    'additional': ['individual.verification.document'],
                    'minimum': ['individual.first_name'],
                })
            })
        })
        super(ConnectAccountTestCase, self).setUp()

    def test_update(self):
        self.check.update(self.connect_account)

        self.assertEqual(self.check.verified, True)
        self.assertEqual(self.check.payouts_enabled, True)
        self.assertEqual(self.check.payments_enabled, True)

    def test_account(self):
        with mock.patch(
                'stripe.Account.retrieve', return_value=self.connect_account
        ) as retrieve:
            self.assertTrue(isinstance(self.check.account, stripe.Account))
            self.assertEqual(self.check.account.id, self.connect_account.id)

            retrieve.assert_called_once_with(self.check.account_id)


class StripeExternalAccountTestCase(BluebottleTestCase):
    def setUp(self):
        account_id = 'some-connect-id'
        external_account_id = 'some-bank-token'
        country = 'NL'

        self.connect_account = stripe.Account(account_id)

        self.connect_account.update({
            'country': country,
            'individual': munch.munchify({
                'first_name': 'Jhon',
                'last_name': 'Example',
                'email': 'jhon@example.com',
            }),
            'requirements': munch.munchify({
                'eventually_due': ['external_accounts'],
                'disabled': False
            }),
            'external_accounts': stripe.ListObject([])
        })

        with mock.patch(
                'stripe.Account.retrieve', return_value=self.connect_account
        ):
            self.check = StripePayoutAccount(
                owner=BlueBottleUserFactory.create(), country=country, account_id=account_id
            )
            self.check.save()

        self.external_account = ExternalAccount(connect_account=self.check, account_id=external_account_id)

        self.connect_external_account = stripe.BankAccount(external_account_id)

        self.connect_external_account.update({
            'object': 'bank_account',
            'account_holder_name': 'Jane Austen',
            'account_holder_type': 'individual',
            'bank_name': 'STRIPE TEST BANK',
            'country': 'US',
            'currency': 'usd',
            'fingerprint': '1JWtPxqbdX5Gamtc',
            'last4': '6789',
            'metadata': {
                'order_id': '6735'
            },
            'routing_number': '110000000',
            'status': 'new',
            'account': 'acct_1032D82eZvKYlo2C'
        })

        super(StripeExternalAccountTestCase, self).setUp()

    def test_retrieve(self):
        with mock.patch(
                'stripe.Account.retrieve', return_value=self.connect_account
        ):
            with mock.patch(
                    'stripe.ListObject.retrieve', return_value=self.connect_external_account
            ) as retrieve_external_account:
                self.assertEqual(
                    self.external_account.account.id,
                    self.connect_external_account.id
                )
                self.assertEqual(
                    self.external_account.account.last4,
                    self.connect_external_account.last4
                )

                retrieve_external_account.assert_called_with(self.external_account.account_id)

    def test_retrieve_already_in_account(self):
        list_object = stripe.ListObject()
        list_object['data'] = [self.connect_external_account]

        self.connect_account.external_accounts = list_object

        with mock.patch(
                'stripe.Account.retrieve', return_value=self.connect_account
        ):
            with mock.patch(
                    'stripe.ListObject.retrieve', return_value=self.connect_external_account
            ) as retrieve_external_account:
                self.assertEqual(
                    self.external_account.account.id,
                    self.connect_external_account.id
                )
                self.assertEqual(
                    self.external_account.account.last4,
                    self.connect_external_account.last4
                )

                self.assertEqual(retrieve_external_account.call_count, 0)
