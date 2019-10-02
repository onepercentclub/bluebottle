import json
import mock

import bunch

from django.urls import reverse

from rest_framework import status

import stripe

from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.funding_stripe.models import StripePaymentProvider
from bluebottle.funding_stripe.tests.factories import (
    StripePayoutAccountFactory,
    ExternalAccountFactory,
    StripePaymentProviderFactory
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class StripePaymentIntentTestCase(BluebottleTestCase):

    def setUp(self):
        super(StripePaymentIntentTestCase, self).setUp()
        StripePaymentProvider.objects.all().delete()
        StripePaymentProviderFactory.create()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()

        self.initiative.transitions.submit()
        self.initiative.transitions.approve()

        self.bank_account = ExternalAccountFactory.create()

        self.funding = FundingFactory.create(initiative=self.initiative, bank_account=self.bank_account)
        self.donation = DonationFactory.create(activity=self.funding, user=None)

        self.intent_url = reverse('stripe-payment-intent-list')

        self.data = {
            'data': {
                'type': 'payments/stripe-payment-intents',
                'relationships': {
                    'donation': {
                        'data': {
                            'type': 'contributions/donations',
                            'id': self.donation.pk,
                        }
                    }
                }
            }
        }

    def test_create_intent(self):
        self.donation.user = self.user
        self.donation.save()

        payment_intent = stripe.PaymentIntent('some intent id')
        payment_intent.update({
            'client_secret': 'some client secret',
        })

        with mock.patch('stripe.PaymentIntent.create', return_value=payment_intent):
            response = self.client.post(self.intent_url, data=json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['intent-id'], payment_intent.id)
        self.assertEqual(data['data']['attributes']['client-secret'], payment_intent.client_secret)
        self.assertEqual(data['included'][0]['attributes']['status'], 'new')

    def test_create_intent_anonymous(self):
        payment_intent = stripe.PaymentIntent('some intent id')
        payment_intent.update({
            'client_secret': 'some client secret',
        })

        with mock.patch('stripe.PaymentIntent.create', return_value=payment_intent):
            response = self.client.post(
                self.intent_url,
                data=json.dumps(self.data),
                HTTP_AUTHORIZATION='Donation {}'.format(self.donation.client_secret)
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['intent-id'], payment_intent.id)
        self.assertEqual(data['data']['attributes']['client-secret'], payment_intent.client_secret)
        self.assertEqual(data['included'][0]['attributes']['status'], 'new')

    def test_create_intent_wrong_token(self):
        payment_intent = stripe.PaymentIntent('some intent id')
        payment_intent.update({
            'client_secret': 'some client secret',
        })

        with mock.patch('stripe.PaymentIntent.create', return_value=payment_intent):
            response = self.client.post(
                self.intent_url,
                data=json.dumps(self.data),
                HTTP_AUTHORIZATION='Donation wrong-token'
            )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_intent_other_user(self):
        self.donation.user = self.user
        self.donation.save()

        response = self.client.post(
            self.intent_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_intent_no_user(self):
        response = self.client.post(
            self.intent_url,
            data=json.dumps(self.data),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class StripeSourcePaymentTestCase(BluebottleTestCase):

    def setUp(self):
        super(StripeSourcePaymentTestCase, self).setUp()
        StripePaymentProviderFactory.create()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()

        self.initiative.transitions.submit()
        self.initiative.transitions.approve()

        self.bank_account = ExternalAccountFactory.create()

        self.funding = FundingFactory.create(initiative=self.initiative, bank_account=self.bank_account)
        self.donation = DonationFactory.create(activity=self.funding, user=None)

        self.payment_url = reverse('stripe-source-payment-list')

        self.data = {
            'data': {
                'type': 'payments/stripe-source-payments',
                'attributes': {
                    'source-token': 'test-token',
                },
                'relationships': {
                    'donation': {
                        'data': {
                            'type': 'contributions/donations',
                            'id': self.donation.pk,
                        }
                    }
                }
            }
        }

    def test_create_payment(self):
        self.donation.user = self.user
        self.donation.save()

        response = self.client.post(self.payment_url, data=json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['source-token'], 'test-token')
        self.assertEqual(data['included'][0]['attributes']['status'], 'new')

    def test_create_payment_anonymous(self):
        response = self.client.post(
            self.payment_url,
            data=json.dumps(self.data),
            HTTP_AUTHORIZATION='Donation {}'.format(self.donation.client_secret)
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['source-token'], 'test-token')
        self.assertEqual(data['included'][0]['attributes']['status'], 'new')

    def test_create_intent_other_user(self):
        self.donation.user = self.user
        self.donation.save()

        response = self.client.post(
            self.payment_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_intent_no_user(self):
        response = self.client.post(
            self.payment_url,
            data=json.dumps(self.data),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ConnectAccountDetailsTestCase(BluebottleTestCase):
    def setUp(self):
        super(ConnectAccountDetailsTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        country = 'NL'

        self.connect_account = stripe.Account('some-connect-id')
        self.connect_account.update({
            'country': country,
            'individual': bunch.bunchify({
                'first_name': 'Jhon',
                'last_name': 'Example',
                'email': 'jhon@example.com',
                'verification': bunch.bunchify({
                    'status': 'pending',
                }),
                'requirements': bunch.bunchify({
                    'eventually_due': ['external_accounts', 'individual.dob.month'],
                })
            }),
            'requirements': bunch.bunchify({
                'eventually_due': ['external_accounts', 'individual.dob.month'],
                'disabled': False
            }),
            'external_accounts': bunch.bunchify({
                'total_count': 0,
                'data': []
            })
        })

        with mock.patch(
            'stripe.Account.retrieve', return_value=self.connect_account
        ):
            self.check = StripePayoutAccountFactory(owner=self.user, country=country, account_id='some-account-id')

        self.url = reverse('connect-account-details')

        self.country_spec = stripe.CountrySpec(country)
        self.country_spec.update({
            'verification_fields': bunch.bunchify({
                'individual': bunch.bunchify({
                    'additional': ['external_accounts'],
                    'minimum': ['individual.first_name'],
                })
            })
        })

        self.data = {
            'data': {
                'type': 'payout-accounts/stripes',
                'id': self.check.pk,
                'attributes': {
                    'token': 'some-account-token',
                    'country': self.check.country,
                }
            }
        }

    def test_create(self):
        self.check.delete()

        connect_account = stripe.Account('some-connect-id')
        connect_account.update({
            'country': self.data['data']['attributes']['country'],
            'individual': bunch.bunchify({
                'first_name': 'Jhon',
                'last_name': 'Example',
                'email': 'jhon@example.com',
                'verification': bunch.bunchify({
                    'status': 'pending',
                }),
                'requirements': bunch.bunchify({
                    'eventually_due': ['external_accounts', 'individual.dob.month'],
                })
            }),
            'requirements': bunch.bunchify({
                'eventually_due': ['external_accounts', 'individual.dob.month'],
                'disabled': False
            }),
            'external_accounts': bunch.bunchify({
                'total_count': 0,
                'data': []
            })
        })
        with mock.patch(
            'stripe.CountrySpec.retrieve', return_value=self.country_spec
        ):
            with mock.patch('stripe.Account.create', return_value=connect_account) as create_account:
                with mock.patch('stripe.Account.modify', return_value=connect_account) as modify_account:
                    response = self.client.post(
                        self.url, data=json.dumps(self.data), user=self.user
                    )
                    create_account.assert_called_with(
                        business_type='individual',
                        country=self.data['data']['attributes']['country'],
                        metadata={'tenant_name': u'test', 'tenant_domain': u'testserver', 'member_id': self.user.pk},
                        settings={
                            'payments': {'statement_descriptor': u''},
                            'payouts': {'schedule': {'interval': 'manual'}}
                        },
                        # business_type='individual',
                        type='custom'
                    )
                    modify_account.assert_called_with(
                        'some-connect-id',
                        account_token='some-account-token'
                    )

        data = json.loads(response.content)

        self.assertEqual(
            data['data']['attributes']['country'],
            self.data['data']['attributes']['country']
        )
        self.assertEqual(
            data['data']['attributes']['disabled'], False
        )
        self.assertEqual(
            data['data']['attributes']['verified'], False
        )
        self.assertEqual(
            data['data']['meta']['required-fields'],
            ['country', 'individual.first_name',
             'document_type', 'individual.verification.document.front']
        )
        self.assertEqual(
            data['data']['attributes']['account']['individual']['first_name'],
            'Jhon',
        )

        self.assertEqual(
            data['data']['relationships']['owner']['data']['id'],
            unicode(self.user.pk)
        )

    def test_create_no_user(self):
        self.check.delete()
        response = self.client.post(
            self.url,
            data=json.dumps(self.data)
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get(self):
        with mock.patch(
            'stripe.CountrySpec.retrieve', return_value=self.country_spec
        ):
            with mock.patch(
                'stripe.Account.retrieve', return_value=self.connect_account
            ) as retrieve:
                response = self.client.get(
                    self.url, user=self.user
                )
                retrieve.assert_called_with(self.check.account_id)

        data = json.loads(response.content)

        self.assertEqual(
            data['data']['attributes']['country'],
            self.check.country
        )
        self.assertEqual(
            data['data']['attributes']['disabled'], False
        )
        self.assertEqual(
            data['data']['attributes']['verified'], False
        )
        self.assertEqual(
            data['data']['meta']['required-fields'],
            ['country', 'individual.first_name',
             'document_type', 'individual.verification.document.front']
        )
        self.assertEqual(
            data['data']['attributes']['account']['individual']['first_name'],
            'Jhon',
        )

        self.assertEqual(
            data['data']['relationships']['owner']['data']['id'],
            unicode(self.user.pk)
        )

    def test_get_no_user(self):
        response = self.client.get(
            self.url,
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_wrong_user(self):
        response = self.client.get(
            self.url,
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch(self):
        with mock.patch(
            'stripe.CountrySpec.retrieve', return_value=self.country_spec
        ):
            with mock.patch(
                'stripe.Account.modify', return_value=self.connect_account
            ) as modify_account:
                response = self.client.patch(
                    self.url,
                    data=json.dumps(self.data),
                    user=self.user
                )
                modify_account.assert_called_with('some-account-id', account_token='some-account-token')

        data = json.loads(response.content)

        self.assertEqual(
            data['data']['attributes']['country'],
            self.check.country
        )
        self.assertEqual(
            data['data']['attributes']['disabled'], False
        )

    def test_patch_wrong_user(self):
        response = self.client.patch(
            self.url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_no_user(self):
        response = self.client.patch(
            self.url,
            data=json.dumps(self.data),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ExternalAccountsTestCase(BluebottleTestCase):
    def setUp(self):
        super(ExternalAccountsTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        account_id = 'some-account-id'
        country = 'NU'

        self.connect_external_account = stripe.BankAccount('some-bank-token')
        self.connect_external_account.update(bunch.bunchify({
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

        external_accounts = stripe.ListObject()
        external_accounts.data = [self.connect_external_account]
        external_accounts.update({
            'total_count': 1,
        })

        self.connect_account = stripe.Account(account_id)
        self.connect_account.update({
            'country': country,
            'external_accounts': external_accounts,
        })

        self.country_spec = stripe.CountrySpec(country)
        self.country_spec.update({
            'verification_fields': bunch.bunchify({
                'individual': bunch.bunchify({
                    'additional': ['individual.verification.document'],
                    'minimum': ['individual.first_name'],
                })
            })
        })

        with mock.patch(
            'stripe.Account.retrieve', return_value=self.connect_account
        ):
            self.check = StripePayoutAccountFactory.create(owner=self.user, account_id=account_id)
        self.external_account = ExternalAccountFactory.create(
            connect_account=self.check,
            account_id='some-external-account-id'
        )

        self.url = reverse('connect-account-details')
        self.external_account_url = reverse('stripe-external-account-list')

    def test_get(self):
        with mock.patch(
            'stripe.CountrySpec.retrieve', return_value=self.country_spec
        ):
            with mock.patch(
                'stripe.Account.retrieve', return_value=self.connect_account
            ) as retrieve:
                with mock.patch(
                    'stripe.ListObject.retrieve', return_value=self.connect_external_account
                ) as retrieve:
                    response = self.client.get(
                        self.url, user=self.user
                    )
                    retrieve.assert_called_with(self.external_account.account_id)
                    self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        external_account = data['included'][1]['attributes']

        self.assertEqual(
            external_account['currency'], self.connect_external_account.currency
        )
        self.assertEqual(
            external_account['country'], self.connect_external_account.country
        )
        self.assertEqual(
            external_account['routing-number'], self.connect_external_account.routing_number
        )
        self.assertEqual(
            external_account['account-holder-name'], self.connect_external_account.account_holder_name
        )
        self.assertEqual(
            external_account['last4'], self.connect_external_account.last4
        )

    def test_create(self):
        data = {
            'data': {
                'type': 'payout-accounts/stripe-external-accounts',
                'attributes': {
                    'token': self.connect_external_account.id
                },
                'relationships': {
                    'connect_account': {
                        'data': {
                            'type': 'payout-accounts/stripes',
                            'id': self.check.pk
                        },
                    }
                }
            }
        }
        with mock.patch(
            'stripe.CountrySpec.retrieve', return_value=self.country_spec
        ):
            with mock.patch(
                'stripe.Account.retrieve', return_value=self.connect_account
            ):
                with mock.patch(
                    'stripe.Account.create_external_account', return_value=self.connect_external_account
                ):
                    response = self.client.post(
                        self.external_account_url, data=json.dumps(data), user=self.user
                    )

        data = json.loads(response.content)
        external_account = data['data']['attributes']

        self.assertEqual(
            external_account['currency'], self.connect_external_account.currency
        )
        self.assertEqual(
            external_account['country'], self.connect_external_account.country
        )
        self.assertEqual(
            external_account['routing-number'], self.connect_external_account.routing_number
        )
        self.assertEqual(
            external_account['account-holder-name'], self.connect_external_account.account_holder_name
        )
        self.assertEqual(
            external_account['last4'], self.connect_external_account.last4
        )
        with mock.patch(
            'stripe.CountrySpec.retrieve', return_value=self.country_spec
        ):
            with mock.patch(
                'stripe.Account.retrieve', return_value=self.connect_account
            ):
                with mock.patch(
                    'stripe.ListObject.retrieve', return_value=self.connect_external_account
                ):
                    response = self.client.get(
                        self.url, user=self.user
                    )

        data = json.loads(response.content)
        external_account = data['included'][1]['attributes']

        self.assertEqual(
            external_account['currency'], self.connect_external_account.currency
        )
        self.assertEqual(
            external_account['country'], self.connect_external_account.country
        )
        self.assertEqual(
            external_account['routing-number'], self.connect_external_account.routing_number
        )
        self.assertEqual(
            external_account['account-holder-name'], self.connect_external_account.account_holder_name
        )
        self.assertEqual(
            external_account['last4'], self.connect_external_account.last4
        )
