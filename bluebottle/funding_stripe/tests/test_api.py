from builtins import str
import json
import mock

import munch
from django.db import connection

from django.urls import reverse

from rest_framework import status

import stripe

from bluebottle.funding.tests.factories import FundingFactory, DonorFactory
from bluebottle.funding_stripe.models import StripePaymentProvider
from bluebottle.funding_stripe.tests.factories import (
    StripePayoutAccountFactory,
    ExternalAccountFactory,
    StripePaymentProviderFactory,
    StripePaymentIntentFactory,
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class StripePaymentIntentListTestCase(BluebottleTestCase):

    def setUp(self):
        super().setUp()
        StripePaymentProvider.objects.all().delete()
        StripePaymentProviderFactory.create()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

        self.bank_account = ExternalAccountFactory.create(
            connect_account=StripePayoutAccountFactory.create(account_id="account-id")
        )

        self.funding = FundingFactory.create(
            initiative=self.initiative, bank_account=self.bank_account
        )
        self.donation = DonorFactory.create(activity=self.funding, user=None)

        self.intent_url = reverse("stripe-payment-intent-list")

        self.data = {
            "data": {
                "type": "payments/stripe-payment-intents",
                "relationships": {
                    "donation": {
                        "data": {
                            "type": "contributors/donations",
                            "id": self.donation.pk,
                        }
                    }
                },
            }
        }

    def test_create_intent(self):
        self.donation.user = self.user
        self.donation.save()

        payment_intent = stripe.PaymentIntent("some intent id")
        payment_intent.update(
            {
                "client_secret": "some client secret",
            }
        )

        with mock.patch(
            "stripe.PaymentIntent.create", return_value=payment_intent
        ) as create_intent:
            response = self.client.post(
                self.intent_url, data=json.dumps(self.data), user=self.user
            )
            create_intent.assert_called_with(
                amount=int(self.donation.amount.amount * 100),
                currency=self.donation.amount.currency,
                metadata={
                    "tenant_name": "test",
                    "activity_id": self.donation.activity.pk,
                    "activity_title": self.donation.activity.title,
                    "tenant_domain": "testserver",
                },
                statement_descriptor="Test",
                statement_descriptor_suffix="Test",
                transfer_data={
                    "destination": self.bank_account.connect_account.account_id
                },
                automatic_payment_methods={"enabled": True},
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data["data"]["attributes"]["intent-id"], payment_intent.id)
        self.assertEqual(
            data["data"]["attributes"]["client-secret"], payment_intent.client_secret
        )
        self.assertEqual(data["included"][0]["attributes"]["status"], "draft")

    def test_create_intent_us(self):
        self.bank_account.connect_account.country = "US"
        self.bank_account.connect_account.save()

        self.donation.user = self.user
        self.donation.save()

        payment_intent = stripe.PaymentIntent("some intent id")
        payment_intent.update(
            {
                "client_secret": "some client secret",
            }
        )

        with mock.patch(
            "stripe.PaymentIntent.create", return_value=payment_intent
        ) as create_intent:
            response = self.client.post(
                self.intent_url, data=json.dumps(self.data), user=self.user
            )
            create_intent.assert_called_with(
                amount=int(self.donation.amount.amount * 100),
                currency=self.donation.amount.currency,
                metadata={
                    "tenant_name": "test",
                    "activity_id": self.donation.activity.pk,
                    "activity_title": self.donation.activity.title,
                    "tenant_domain": "testserver",
                },
                on_behalf_of=self.bank_account.connect_account.account_id,
                statement_descriptor="Test",
                statement_descriptor_suffix="Test",
                transfer_data={
                    "destination": self.bank_account.connect_account.account_id
                },
                automatic_payment_methods={"enabled": True},
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data["data"]["attributes"]["intent-id"], payment_intent.id)
        self.assertEqual(
            data["data"]["attributes"]["client-secret"], payment_intent.client_secret
        )
        self.assertEqual(data["included"][0]["attributes"]["status"], "draft")

    def test_create_intent_anonymous(self):
        payment_intent = stripe.PaymentIntent("some intent id")
        payment_intent.update(
            {
                "client_secret": self.donation.client_secret,
            }
        )

        with mock.patch("stripe.PaymentIntent.create", return_value=payment_intent):
            self.data["data"]["attributes"] = {
                "client_secret": self.donation.client_secret
            }
            response = self.client.post(self.intent_url, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data["data"]["attributes"]["intent-id"], payment_intent.id)
        self.assertEqual(
            data["data"]["attributes"]["client-secret"], payment_intent.client_secret
        )
        self.assertEqual(data["included"][0]["attributes"]["status"], "draft")

    def test_create_intent_wrong_token(self):
        payment_intent = stripe.PaymentIntent("some intent id")
        payment_intent.update(
            {
                "client_secret": "some client secret",
            }
        )

        with mock.patch("stripe.PaymentIntent.create", return_value=payment_intent):
            self.data["data"]["attributes"] = {"client_secret": "wrong secret"}
            response = self.client.post(
                self.intent_url,
                data=json.dumps(self.data),
            )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_intent_other_user(self):
        self.donation.user = self.user
        self.donation.save()

        response = self.client.post(
            self.intent_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create(),
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_intent_no_user(self):
        response = self.client.post(
            self.intent_url,
            data=json.dumps(self.data),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class StripePaymentIntentDetailTestCase(BluebottleTestCase):

    def setUp(self):
        super().setUp()
        StripePaymentProvider.objects.all().delete()
        StripePaymentProviderFactory.create()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

        self.bank_account = ExternalAccountFactory.create(
            connect_account=StripePayoutAccountFactory.create(account_id="account-id")
        )

        self.funding = FundingFactory.create(
            initiative=self.initiative, bank_account=self.bank_account
        )
        self.donation = DonorFactory.create(activity=self.funding)
        self.intent = StripePaymentIntentFactory.create(
            donation=self.donation,
            client_secret='some-client-secret'
        )

        self.intent_url = reverse(
            "stripe-payment-intent-detail", args=(self.intent.pk, )
        )

        self.payment_intent = stripe.PaymentIntent("some intent id")
        self.payment_intent.update(
            {
                "client_secret": self.intent.client_secret,
                "charges": []
            }
        )

    def test_get_user(self):
        with mock.patch(
            "stripe.PaymentIntent.retrieve", return_value=self.payment_intent
        ):
            response = self.client.get(self.intent_url, user=self.donation.user)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_other_user(self):
        with mock.patch(
            "stripe.PaymentIntent.retrieve", return_value=self.payment_intent
        ):
            response = self.client.get(
                self.intent_url, user=BlueBottleUserFactory.create()
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_anonymous(self):
        with mock.patch(
            "stripe.PaymentIntent.retrieve", return_value=self.payment_intent
        ):
            response = self.client.get(self.intent_url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_client_secret(self):
        self.donation.user = None
        self.donation.save()

        with mock.patch(
            "stripe.PaymentIntent.retrieve", return_value=self.payment_intent
        ):
            response = self.client.get(
                self.intent_url,
                HTTP_AUTHORIZATION=f'donation {self.donation.client_secret}'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_wrong_client_secret(self):
        self.donation.user = None
        self.donation.save()

        with mock.patch(
            "stripe.PaymentIntent.retrieve", return_value=self.payment_intent
        ):
            response = self.client.get(
                self.intent_url, HTTP_AUTHORIZATION='donation some-other-secret'
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ConnectAccountDetailsTestCase(BluebottleTestCase):
    def setUp(self):
        super(ConnectAccountDetailsTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        country = "NL"
        self.activity = FundingFactory.create(owner=self.user)

        self.stripe_connect_account = stripe.Account("some-connect-id")
        self.stripe_connect_account.update(
            {
                "country": country,
                "individual": munch.munchify(
                    {
                        "first_name": "Jhon",
                        "last_name": "Example",
                        "email": "jhon@example.com",
                        "verification": munch.munchify(
                            {
                                "status": "pending",
                            }
                        ),
                        "requirements": munch.munchify(
                            {
                                "eventually_due": [
                                    "external_accounts",
                                    "individual.dob.month",
                                ],
                                "currently_due": [],
                                "past_due": [],
                            }
                        ),
                    }
                ),
                "requirements": munch.munchify(
                    {
                        "eventually_due": ["external_accounts", "individual.dob.month"],
                        "disabled": False,
                    }
                ),
                "external_accounts": munch.munchify({"total_count": 0, "data": []}),
            }
        )

        with mock.patch(
            "stripe.Account.retrieve", return_value=self.stripe_connect_account
        ):
            self.connect_account = StripePayoutAccountFactory(
                owner=self.user, country=country, account_id="some-account-id"
            )

        self.account_list_url = reverse("connect-account-list")
        self.account_url = reverse(
            "connect-account-detail", args=(self.connect_account.pk,)
        )

        self.country_spec = stripe.CountrySpec(country)
        self.country_spec.update(
            {
                "verification_fields": munch.munchify(
                    {
                        "individual": munch.munchify(
                            {
                                "additional": ["external_accounts"],
                                "minimum": ["individual.first_name"],
                            }
                        )
                    }
                )
            }
        )

        self.data = {
            "data": {
                "type": "payout-accounts/stripes",
                "id": self.connect_account.pk,
                "attributes": {
                    "token": "some-account-token",
                    "country": self.connect_account.country,
                },
            }
        }

    def test_create(self):
        self.connect_account.delete()
        tenant = connection.tenant
        tenant.name = "tst"
        tenant.save()

        connect_account = stripe.Account("some-connect-id")
        connect_account.update(
            {
                "country": self.data["data"]["attributes"]["country"],
                "business_type": "individual",
                "individual": munch.munchify(
                    {
                        "first_name": "Jhon",
                        "last_name": "Example",
                        "email": "jhon@example.com",
                        "verification": munch.munchify(
                            {
                                "status": "pending",
                            }
                        ),
                        "requirements": munch.munchify(
                            {
                                "eventually_due": [
                                    "external_accounts",
                                    "individual.dob.month",
                                ],
                                "currently_due": [],
                                "past_due": [],
                            }
                        ),
                    }
                ),
                "requirements": munch.munchify(
                    {
                        "eventually_due": ["external_accounts", "individual.dob.month"],
                        "disabled": False,
                    }
                ),
                "external_accounts": munch.munchify({"total_count": 0, "data": []}),
            }
        )
        with mock.patch(
            "stripe.CountrySpec.retrieve", return_value=self.country_spec
        ), mock.patch(
            "stripe.Account.create", return_value=connect_account
        ) as create_account, mock.patch(
            "stripe.Account.modify", return_value=connect_account
        ), mock.patch(
            "stripe.Account.retrieve", return_value=connect_account
        ):
            response = self.client.post(
                self.account_list_url, data=json.dumps(self.data), user=self.user
            )
            call = create_account.call_args.kwargs

            self.assertEqual(call["country"], "NL")
            self.assertEqual(call["type"], "custom")
            self.assertEqual(call["business_type"], "individual")
            self.assertEqual(
                call["settings"],
                {
                    "card_payments": {"statement_descriptor_prefix": "tst--"},
                    "payments": {"statement_descriptor": "tst--"},
                    "payouts": {
                        "statement_descriptor": "tst--",
                        "schedule": {"interval": "manual"},
                    },
                },
            )
            self.assertEqual(
                call["metadata"],
                {
                    "tenant_name": "test",
                    "tenant_domain": "testserver",
                    "member_id": self.user.pk,
                },
            )

            self.assertEqual(
                call["business_profile"],
                {"url": self.activity.get_absolute_url(), "mcc": "8398"},
            )
            self.assertEqual(call["individual"], {"email": self.user.email})
            self.assertEqual(
                call["capabilities"],
                {
                    "transfers": {"requested": True},
                    "card_payments": {"requested": True},
                },
            )

        data = json.loads(response.content)

        self.assertEqual(
            data["data"]["attributes"]["country"],
            self.data["data"]["attributes"]["country"],
        )
        self.assertEqual(data["data"]["attributes"]["verified"], False)
        self.assertEqual(data["data"]["attributes"]["payouts-enabled"], False)
        self.assertEqual(data["data"]["attributes"]["payments-enabled"], False)

        self.assertEqual(
            data["data"]["relationships"]["owner"]["data"]["id"], str(self.user.pk)
        )

    def test_create_no_user(self):

        self.connect_account.delete()
        response = self.client.post(self.account_url, data=json.dumps(self.data))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get(self):
        response = self.client.get(self.account_url, user=self.user)

        data = json.loads(response.content)

        self.assertEqual(
            data["data"]["attributes"]["country"], self.connect_account.country
        )
        self.assertEqual(data["data"]["attributes"]["verified"], False)

        self.assertEqual(
            data["data"]["relationships"]["owner"]["data"]["id"], str(self.user.pk)
        )

    def test_get_no_user(self):
        response = self.client.get(
            self.account_url,
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_wrong_user(self):
        response = self.client.get(
            self.account_url, user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_bank_accounts_no_user(self):
        response = self.client.get(self.account_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_bank_accounts_other_user(self):
        response = self.client.get(
            self.account_list_url, user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["data"]), 0)


class ExternalAccountsTestCase(BluebottleTestCase):
    def setUp(self):
        super(ExternalAccountsTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        account_id = "some-account-id"
        country = "NU"
        self.activity = FundingFactory.create(owner=self.user)

        self.connect_external_account = stripe.BankAccount("some-bank-token")
        self.connect_external_account.update(
            munch.munchify(
                {
                    "object": "bank_account",
                    "account_holder_name": "Jane Austen",
                    "account_holder_type": "individual",
                    "bank_name": "STRIPE TEST BANK",
                    "country": "US",
                    "currency": "usd",
                    "fingerprint": "1JWtPxqbdX5Gamtc",
                    "last4": "6789",
                    "metadata": {"order_id": "6735"},
                    "routing_number": "110000000",
                    "status": "new",
                    "account": "acct_1032D82eZvKYlo2C",
                }
            )
        )

        external_accounts = stripe.ListObject()
        external_accounts.data = [self.connect_external_account]
        external_accounts.update(
            {
                "total_count": 1,
            }
        )

        self.stripe_connect_account = stripe.Account(account_id)
        self.stripe_connect_account.update(
            {
                "country": country,
                "external_accounts": external_accounts,
                "requirements": munch.munchify({"eventually_due": ["document_type"]}),
            }
        )

        self.country_spec = stripe.CountrySpec(country)
        self.country_spec.update(
            {
                "verification_fields": munch.munchify(
                    {
                        "individual": munch.munchify(
                            {
                                "additional": ["individual.verification.document"],
                                "minimum": ["individual.first_name"],
                            }
                        )
                    }
                )
            }
        )

        with mock.patch(
            "stripe.Account.retrieve", return_value=self.stripe_connect_account
        ):
            self.connect_account = StripePayoutAccountFactory.create(
                owner=self.activity.owner, account_id=account_id
            )
        self.external_account = ExternalAccountFactory.create(
            connect_account=self.connect_account, account_id="some-external-account-id"
        )

        self.url = reverse("connect-account-detail", args=(self.connect_account.pk,))
        self.external_account_url = reverse("stripe-external-account-list")
        self.external_account_detail_url = reverse(
            "stripe-external-account-details", args=(self.external_account.pk,)
        )

    def test_get_accounts_no_user(self):
        response = self.client.get(self.external_account_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_accounts_other_user(self):
        response = self.client.get(
            self.external_account_url, user=BlueBottleUserFactory.create()
        )
        self.assertEqual(len(response.json()["data"]), 0)

    def test_get(self):
        with mock.patch(
            "stripe.Account.retrieve", return_value=self.stripe_connect_account
        ) as retrieve, mock.patch(
            "stripe.ListObject.retrieve", return_value=self.connect_external_account
        ) as retrieve:
            response = self.client.get(self.url, user=self.user)
            retrieve.assert_called_with(self.external_account.account_id)
            self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        external_account = data["included"][1]["attributes"]

        self.assertEqual(
            external_account["currency"], self.connect_external_account.currency
        )
        self.assertEqual(
            external_account["country"], self.connect_external_account.country
        )
        self.assertEqual(
            external_account["routing-number"],
            self.connect_external_account.routing_number,
        )
        self.assertEqual(
            external_account["account-holder-name"],
            self.connect_external_account.account_holder_name,
        )
        self.assertEqual(external_account["last4"], self.connect_external_account.last4)

    def test_create(self):
        data = {
            "data": {
                "type": "payout-accounts/stripe-external-accounts",
                "attributes": {"token": self.connect_external_account.id},
                "relationships": {
                    "connect_account": {
                        "data": {
                            "type": "payout-accounts/stripes",
                            "id": self.connect_account.pk,
                        },
                    }
                },
            }
        }
        with mock.patch(
            "stripe.CountrySpec.retrieve", return_value=self.country_spec
        ), mock.patch(
            "stripe.Account.retrieve", return_value=self.stripe_connect_account
        ), mock.patch(
            "stripe.Account.create_external_account",
            return_value=self.connect_external_account,
        ):
            response = self.client.post(
                self.external_account_url, data=json.dumps(data), user=self.user
            )
            self.assertEqual(response.status_code, 201)

        data = json.loads(response.content)
        external_account = data["data"]["attributes"]

        self.assertEqual(
            external_account["currency"], self.connect_external_account.currency
        )
        self.assertEqual(
            external_account["country"], self.connect_external_account.country
        )
        self.assertEqual(
            external_account["routing-number"],
            self.connect_external_account.routing_number,
        )
        self.assertEqual(
            external_account["account-holder-name"],
            self.connect_external_account.account_holder_name,
        )
        self.assertEqual(external_account["last4"], self.connect_external_account.last4)
        with mock.patch(
            "stripe.CountrySpec.retrieve", return_value=self.country_spec
        ), mock.patch(
            "stripe.Account.retrieve", return_value=self.stripe_connect_account
        ), mock.patch(
            "stripe.ListObject.retrieve", return_value=self.connect_external_account
        ):
            response = self.client.get(self.url, user=self.user)

        data = json.loads(response.content)
        external_account = data["included"][1]["attributes"]

        self.assertEqual(
            external_account["currency"], self.connect_external_account.currency
        )
        self.assertEqual(
            external_account["country"], self.connect_external_account.country
        )
        self.assertEqual(
            external_account["routing-number"],
            self.connect_external_account.routing_number,
        )
        self.assertEqual(
            external_account["account-holder-name"],
            self.connect_external_account.account_holder_name,
        )
        self.assertEqual(external_account["last4"], self.connect_external_account.last4)

    def test_get_external_account_detail(self):
        response = self.client.get(
            self.external_account_detail_url,
            user=self.external_account.owner
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()['data']['attributes']['account-id'],
            'some-external-account-id'
        )

    def test_get_external_account_anonymous(self):
        response = self.client.get(
            self.external_account_detail_url
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_external_account_other_user(self):
        response = self.client.get(
            self.external_account_detail_url,
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_new_extenal(self):
        data = {
            'data': {
                "attributes": {
                    "account-holder-name": "Tes Ting",
                    "token": "btok_1234"
                },
                "type": "payout-accounts/stripe-external-accounts",
                "relationships": {
                    "connect-account": {
                        "data": {
                            "type": "payout-accounts/stripes",
                            "id": self.connect_account.id
                        }
                    }
                }
            }
        }

        connect_external_account = stripe.BankAccount('some-bank-token')
        connect_external_account.update(munch.munchify({
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
        }))

        with mock.patch(
            'stripe.CountrySpec.retrieve', return_value=self.country_spec
        ), mock.patch(
            'stripe.Account.retrieve', return_value=self.stripe_connect_account
        ), mock.patch(
            'stripe.Account.create_external_account', return_value=connect_external_account
        ):
            response = self.client.post(
                self.external_account_url, data=json.dumps(data), user=self.user
            )
            self.assertEqual(response.status_code, 201)

        data = json.loads(response.content)
        external_account = data['data']['attributes']
        self.assertEqual(external_account['status'], 'unverified')
