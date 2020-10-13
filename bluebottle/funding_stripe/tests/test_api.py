from builtins import str
import json
import mock

import munch
from django.db import connection

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
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

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

        with mock.patch('stripe.PaymentIntent.create', return_value=payment_intent) as create_intent:
            response = self.client.post(self.intent_url, data=json.dumps(self.data), user=self.user)
            create_intent.assert_called_with(
                amount=int(self.donation.amount.amount * 100),
                currency=self.donation.amount.currency,
                metadata={
                    'tenant_name': u'test',
                    'activity_id': self.donation.activity.pk,
                    'activity_title': self.donation.activity.title,
                    'tenant_domain': u'testserver'
                },
                statement_descriptor=u'Test',
                statement_descriptor_suffix=u'Test',
                transfer_data={
                    'destination': self.bank_account.connect_account.account_id
                }
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['intent-id'], payment_intent.id)
        self.assertEqual(data['data']['attributes']['client-secret'], payment_intent.client_secret)
        self.assertEqual(data['included'][0]['attributes']['status'], 'new')

    def test_create_intent_us(self):
        self.bank_account.connect_account.account.country = 'US'
        self.bank_account.connect_account.country = 'US'
        self.bank_account.connect_account.save()

        self.donation.user = self.user
        self.donation.save()

        payment_intent = stripe.PaymentIntent('some intent id')
        payment_intent.update({
            'client_secret': 'some client secret',
        })

        with mock.patch('stripe.PaymentIntent.create', return_value=payment_intent) as create_intent:
            response = self.client.post(self.intent_url, data=json.dumps(self.data), user=self.user)
            create_intent.assert_called_with(
                amount=int(self.donation.amount.amount * 100),
                currency=self.donation.amount.currency,
                metadata={
                    'tenant_name': u'test',
                    'activity_id': self.donation.activity.pk,
                    'activity_title': self.donation.activity.title,
                    'tenant_domain': u'testserver'
                },
                on_behalf_of=self.bank_account.connect_account.account_id,
                statement_descriptor=u'Test',
                statement_descriptor_suffix=u'Test',
                transfer_data={
                    'destination': self.bank_account.connect_account.account_id
                }
            )

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
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

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

        with mock.patch(
            'stripe.Source.modify'
        ):
            response = self.client.post(self.payment_url, data=json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['source-token'], 'test-token')
        self.assertEqual(data['included'][0]['attributes']['status'], 'new')

    def test_create_payment_anonymous(self):
        with mock.patch(
            'stripe.Source.modify'
        ):
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

        self.stripe_connect_account = stripe.Account('some-connect-id')
        self.stripe_connect_account.update({
            'country': country,
            'individual': munch.munchify({
                'first_name': 'Jhon',
                'last_name': 'Example',
                'email': 'jhon@example.com',
                'verification': munch.munchify({
                    'status': 'pending',
                }),
                'requirements': munch.munchify({
                    'eventually_due': ['external_accounts', 'individual.dob.month'],
                    'currently_due': [],
                    'past_due': [],
                })
            }),
            'requirements': munch.munchify({
                'eventually_due': ['external_accounts', 'individual.dob.month'],
                'disabled': False
            }),
            'external_accounts': munch.munchify({
                'total_count': 0,
                'data': []
            })
        })

        with mock.patch(
            'stripe.Account.retrieve', return_value=self.stripe_connect_account
        ):
            self.connect_account = StripePayoutAccountFactory(
                owner=self.user,
                country=country,
                account_id='some-account-id'
            )

        self.account_list_url = reverse('connect-account-list')
        self.account_url = reverse('connect-account-details', args=(self.connect_account.id,))

        self.country_spec = stripe.CountrySpec(country)
        self.country_spec.update({
            'verification_fields': munch.munchify({
                'individual': munch.munchify({
                    'additional': ['external_accounts'],
                    'minimum': ['individual.first_name'],
                })
            })
        })

        self.data = {
            'data': {
                'type': 'payout-accounts/stripes',
                'id': self.connect_account.pk,
                'attributes': {
                    'token': 'some-account-token',
                    'country': self.connect_account.country,
                }
            }
        }

    def test_create(self):
        self.connect_account.delete()
        tenant = connection.tenant
        tenant.name = 'tst'
        tenant.save()

        connect_account = stripe.Account('some-connect-id')
        connect_account.update({
            'country': self.data['data']['attributes']['country'],
            'individual': munch.munchify({
                'first_name': 'Jhon',
                'last_name': 'Example',
                'email': 'jhon@example.com',
                'verification': munch.munchify({
                    'status': 'pending',
                }),
                'requirements': munch.munchify({
                    'eventually_due': ['external_accounts', 'individual.dob.month'],
                    'currently_due': [],
                    'past_due': [],
                })
            }),
            'requirements': munch.munchify({
                'eventually_due': ['external_accounts', 'individual.dob.month'],
                'disabled': False
            }),
            'external_accounts': munch.munchify({
                'total_count': 0,
                'data': []
            })
        })
        with mock.patch(
            'stripe.CountrySpec.retrieve', return_value=self.country_spec
        ), mock.patch(
            'stripe.Account.create', return_value=connect_account
        ) as create_account, mock.patch(
            'stripe.Account.modify', return_value=connect_account
        ) as modify_account, mock.patch(
            'stripe.Account.retrieve', return_value=connect_account
        ):
            response = self.client.post(
                self.account_list_url, data=json.dumps(self.data), user=self.user
            )
            create_account.assert_called_with(
                business_profile={'url': 'https://testserver', 'mcc': '8398'},
                business_type='individual',
                country=self.data['data']['attributes']['country'],
                metadata={'tenant_name': 'test', 'tenant_domain': 'testserver', 'member_id': self.user.pk},
                requested_capabilities=['transfers'],
                settings={
                    'card_payments': {
                        'statement_descriptor_prefix': u'tst--'
                    },
                    'payments': {
                        'statement_descriptor': u'tst--'
                    },
                    'payouts': {
                        'statement_descriptor': u'tst--',
                        'schedule': {'interval': 'manual'}
                    }
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
            [
                u'country',
                u'external_accounts',
                u'individual.verification.additional_document',
                u'document_type',
                u'individual.verification.document.front',
                u'individual.dob'
            ]
        )
        self.assertEqual(
            data['data']['attributes']['account']['individual']['first_name'],
            'Jhon',
        )

        self.assertEqual(
            data['data']['relationships']['owner']['data']['id'],
            str(self.user.pk)
        )

    def test_create_us(self):
        self.connect_account.delete()
        tenant = connection.tenant
        tenant.name = 'tst'
        tenant.save()

        connect_account = stripe.Account('some-connect-id')
        connect_account.update({
            'country': self.data['data']['attributes']['country'],
            'individual': munch.munchify({
                'first_name': 'Jhon',
                'last_name': 'Example',
                'email': 'jhon@example.com',
                'verification': munch.munchify({
                    'status': 'pending',
                }),
                'requirements': munch.munchify({
                    'eventually_due': ['external_accounts', 'individual.dob.month'],
                    'currently_due': [],
                    'past_due': [],
                })
            }),
            'requirements': munch.munchify({
                'eventually_due': ['external_accounts', 'individual.dob.month'],
                'disabled': False
            }),
            'external_accounts': munch.munchify({
                'total_count': 0,
                'data': []
            })
        })

        self.data['data']['attributes']['country'] = 'US'

        with mock.patch(
                'stripe.CountrySpec.retrieve', return_value=self.country_spec
        ), mock.patch(
            'stripe.Account.create', return_value=connect_account
        ) as create_account, mock.patch(
            'stripe.Account.modify', return_value=connect_account
        ) as modify_account, mock.patch(
            'stripe.Account.retrieve', return_value=connect_account
        ):
            self.client.post(
                self.account_list_url, data=json.dumps(self.data), user=self.user
            )
            create_account.assert_called_with(
                business_profile={'url': 'https://testserver', 'mcc': '8398'},
                business_type='individual',
                country=self.data['data']['attributes']['country'],
                metadata={'tenant_name': 'test', 'tenant_domain': 'testserver', 'member_id': self.user.pk},
                requested_capabilities=['transfers', 'card_payments'],
                settings={
                    'card_payments': {
                        'statement_descriptor_prefix': u'tst--'
                    },
                    'payments': {
                        'statement_descriptor': u'tst--'
                    },
                    'payouts': {
                        'statement_descriptor': u'tst--',
                        'schedule': {'interval': 'manual'}
                    }
                },
                # business_type='individual',
                type='custom'
            )
            modify_account.assert_called_with(
                'some-connect-id',
                account_token='some-account-token'
            )

    def test_create_no_user(self):
        self.connect_account.delete()
        response = self.client.post(
            self.account_url,
            data=json.dumps(self.data)
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get(self):
        with mock.patch(
            'stripe.CountrySpec.retrieve', return_value=self.country_spec
        ), mock.patch(
            'stripe.Account.retrieve', return_value=self.stripe_connect_account
        ) as retrieve:
            response = self.client.get(
                self.account_url, user=self.user
            )
            retrieve.assert_called_with(self.connect_account.account_id)

        data = json.loads(response.content)

        self.assertEqual(
            data['data']['attributes']['country'],
            self.connect_account.country
        )
        self.assertEqual(
            data['data']['attributes']['disabled'], False
        )
        self.assertEqual(
            data['data']['attributes']['verified'], False
        )
        self.assertEqual(
            data['data']['meta']['required-fields'],
            [
                u'country',
                u'external_accounts',
                u'individual.verification.additional_document',
                u'document_type',
                u'individual.verification.document.front',
                u'individual.dob'
            ]
        )
        self.assertEqual(
            data['data']['attributes']['account']['individual']['first_name'],
            'Jhon',
        )

        self.assertEqual(
            data['data']['relationships']['owner']['data']['id'],
            str(self.user.pk)
        )

    def test_get_verification_error(self):
        error = {
            "reason": (
                "The date of birth (DOB) on the document does not match "
                "the DOB on the account. Please upload a document with a "
                "DOB that matches the DOB on the account. You can also "
                "update the DOB on the account."
            ),
            "code": "verification_document_dob_mismatch",
            "requirement": "individual.verification.document"
        }
        self.stripe_connect_account.update({
            'requirements': munch.munchify({
                'eventually_due': ['external_accounts', 'individual.dob.month'],
                'errors': [error],
                'disabled': False
            }),
        })

        with mock.patch(
            'stripe.CountrySpec.retrieve', return_value=self.country_spec
        ), mock.patch(
            'stripe.Account.retrieve', return_value=self.stripe_connect_account
        ) as retrieve:
            response = self.client.get(
                self.account_url, user=self.user
            )
            retrieve.assert_called_with(self.connect_account.account_id)

        data = json.loads(response.content)
        self.assertEqual(
            data['data']['meta']['errors'][0]['source']['pointer'],
            '/data/attributes/individual/verification/document/front'
        )
        self.assertEqual(
            data['data']['meta']['errors'][0]['title'],
            error['reason']
        )
        self.assertEqual(
            data['data']['meta']['errors'][0]['code'],
            error['code']
        )

    def test_get_no_user(self):
        response = self.client.get(
            self.account_url,
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_wrong_user(self):
        response = self.client.get(
            self.account_url,
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch(self):
        with mock.patch(
            'stripe.CountrySpec.retrieve', return_value=self.country_spec
        ), mock.patch(
            'stripe.Account.modify', return_value=self.stripe_connect_account
        ) as modify_account:
            response = self.client.patch(
                self.account_url,
                data=json.dumps(self.data),
                user=self.user
            )
            modify_account.assert_called_with('some-account-id', account_token='some-account-token')

        data = json.loads(response.content)

        self.assertEqual(
            data['data']['attributes']['country'],
            self.connect_account.country
        )
        self.assertEqual(
            data['data']['attributes']['disabled'], False
        )

    def test_patch_wrong_user(self):
        response = self.client.patch(
            self.account_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_no_user(self):
        response = self.client.patch(
            self.account_url,
            data=json.dumps(self.data),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_bank_accounts_no_user(self):
        response = self.client.get(
            self.account_list_url
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_bank_accounts_other_user(self):
        response = self.client.get(
            self.account_list_url,
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class ExternalAccountsTestCase(BluebottleTestCase):
    def setUp(self):
        super(ExternalAccountsTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        account_id = 'some-account-id'
        country = 'NU'

        self.connect_external_account = stripe.BankAccount('some-bank-token')
        self.connect_external_account.update(munch.munchify({
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

        self.stripe_connect_account = stripe.Account(account_id)
        self.stripe_connect_account.update({
            'country': country,
            'external_accounts': external_accounts,
            'requirements': munch.munchify({
                'eventually_due': ['document_type']
            })
        })

        self.country_spec = stripe.CountrySpec(country)
        self.country_spec.update({
            'verification_fields': munch.munchify({
                'individual': munch.munchify({
                    'additional': ['individual.verification.document'],
                    'minimum': ['individual.first_name'],
                })
            })
        })

        with mock.patch(
            'stripe.Account.retrieve', return_value=self.stripe_connect_account
        ):
            self.connect_account = StripePayoutAccountFactory.create(owner=self.user, account_id=account_id)
        self.external_account = ExternalAccountFactory.create(
            connect_account=self.connect_account,
            account_id='some-external-account-id'
        )

        self.url = reverse('connect-account-details', args=(self.connect_account.id, ))
        self.external_account_url = reverse('stripe-external-account-list')
        self.external_account_detail_url = reverse(
            'stripe-external-account-details',
            args=(self.external_account.pk, )
        )

    def test_get_accounts_no_user(self):
        response = self.client.get(
            self.external_account_url
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_accounts_other_user(self):
        response = self.client.get(
            self.external_account_url,
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get(self):
        with mock.patch(
            'stripe.CountrySpec.retrieve', return_value=self.country_spec
        ), mock.patch(
            'stripe.Account.retrieve', return_value=self.stripe_connect_account
        ) as retrieve, mock.patch(
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
                            'id': self.connect_account.pk
                        },
                    }
                }
            }
        }
        with mock.patch(
            'stripe.CountrySpec.retrieve', return_value=self.country_spec
        ), mock.patch(
            'stripe.Account.retrieve', return_value=self.stripe_connect_account
        ), mock.patch(
            'stripe.Account.create_external_account', return_value=self.connect_external_account
        ):
            response = self.client.post(
                self.external_account_url, data=json.dumps(data), user=self.user
            )
            self.assertEqual(response.status_code, 201)

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
        ), mock.patch(
            'stripe.Account.retrieve', return_value=self.stripe_connect_account
        ), mock.patch(
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
