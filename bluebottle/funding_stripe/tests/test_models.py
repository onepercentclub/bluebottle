import munch
import mock
import stripe
from bluebottle.funding_stripe.tests.factories import StripePayoutAccountFactory
from django.db import ProgrammingError, connection

from bluebottle.funding_stripe.models import (
    StripePayoutAccount, ExternalAccount
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class ConnectAccountTestCase(BluebottleTestCase):
    def setUp(self):
        account_id = 'some-connect-id'
        self.check = StripePayoutAccount(owner=BlueBottleUserFactory.create(), country='NL', account_id=account_id)

        self.connect_account = stripe.Account(account_id)
        self.connect_account.update({
            'country': self.check.country,
            'individual': munch.munchify({
                'first_name': 'Jhon',
                'last_name': 'Example',
                'email': 'jhon@example.com',
                'verification': {
                    'status': 'verified',
                },
                'requirements': munch.munchify({
                    'eventually_due': [
                        'external_accounts',
                        'individual.verification.document',
                        'document_type',
                    ]
                }),
            }),
            'requirements': munch.munchify({
                'eventually_due': [
                    'external_accounts',
                    'individual.verification.document.front',
                    'document_type',
                ],
                'disabled': False
            }),
            'external_accounts': munch.munchify({
                'total_count': 0,
                'data': []
            })
        })

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

    def test_save(self):
        self.check.account_id = None
        tenant = connection.tenant
        tenant.name = 'GoDoGood'
        tenant.save()

        with mock.patch(
                'stripe.Account.create', return_value=self.connect_account
        ) as create:
            self.check.save()
            create.assert_called_with(
                business_profile={'url': 'https://testserver', 'mcc': '8398'},
                business_type='individual',
                country=self.check.country,
                metadata={'tenant_name': u'test', 'tenant_domain': u'testserver', 'member_id': self.check.owner.pk},
                requested_capabilities=['transfers'],
                settings={
                    'card_payments': {
                        'statement_descriptor_prefix': 'GoDoGood'
                    },
                    'payments': {
                        'statement_descriptor': 'GoDoGood'
                    },
                    'payouts': {
                        'statement_descriptor': 'GoDoGood',
                        'schedule': {'interval': 'manual'}
                    }
                },
                type='custom'
            )

            self.assertEqual(self.check.account.id, self.connect_account.id)

            self.assertEqual(
                self.check.account_id,
                self.connect_account.id
            )

    def test_save_already_created(self):
        with mock.patch(
                'stripe.Account.create', return_value=self.connect_account
        ) as create:
            with mock.patch(
                    'stripe.Account.retrieve', return_value=self.connect_account
            ):
                self.check.save()
                self.assertEqual(create.call_count, 0)

    def test_update(self):
        with mock.patch(
                'stripe.Account.retrieve', return_value=self.connect_account
        ):
            self.check.save()

        token = 'some-token'

        with mock.patch(
                'stripe.Account.modify', return_value=self.connect_account
        ) as modify:
            self.check.update(token)
            self.assertEqual(self.check.account.id, self.connect_account.id)
            modify.assert_called_with(self.check.account_id, account_token=token)

    def test_account(self):
        with mock.patch(
                'stripe.Account.retrieve', return_value=self.connect_account
        ) as retrieve:
            self.assertTrue(isinstance(self.check.account, stripe.Account))
            self.assertEqual(self.check.account.id, self.connect_account.id)

            retrieve.assert_called_once_with(self.check.account_id)

    def test_complete(self):
        self.connect_account.individual.requirements.eventually_due = []
        with mock.patch(
                'stripe.Account.retrieve', return_value=self.connect_account
        ):
            self.assertTrue(self.check.complete)

    def test_not_verified(self):
        with mock.patch(
                'stripe.Account.retrieve', return_value=self.connect_account
        ):
            self.assertFalse(self.check.verified)

    def test_required(self):
        with mock.patch(
                'stripe.Account.retrieve', return_value=self.connect_account
        ):
            self.check.save()
            self.assertEqual(
                list(self.check.required),
                [
                    'individual.verification.document.front',
                    'document_type',
                    'individual.verification.additional_document',
                    'external_account'
                ]
            )

    def test_disabled(self):
        self.connect_account.requirements.disabled = True
        with mock.patch(
                'stripe.Account.retrieve', return_value=self.connect_account
        ):
            self.assertTrue(self.check.disabled)

    def test_not_disabled(self):
        with mock.patch(
                'stripe.Account.retrieve', return_value=self.connect_account
        ):
            self.assertFalse(self.check.disabled)

    def test_country_spec(self):
        account = StripePayoutAccountFactory.create(country='BE')
        self.assertEqual(
            account.document_spec['id'],
            'BE'
        )
        self.assertEqual(
            account.document_spec['supported_document_types'],
            [u'passport', u'id-card', u'drivers-license']
        )
        self.assertEqual(
            account.document_spec['document_types_requiring_back'],
            [u'id-card']
        )
        account = StripePayoutAccountFactory.create(country='NL')
        self.assertEqual(
            account.document_spec['id'],
            'NL'
        )
        self.assertEqual(
            account.document_spec['supported_document_types'],
            [u'passport', u'id-card', u'drivers-license']
        )
        self.assertEqual(
            account.document_spec['document_types_requiring_back'],
            [u'id-card', u'drivers-license']
        )
        account = StripePayoutAccountFactory.create(country='XX')
        self.assertEqual(
            account.document_spec['id'],
            'DEFAULT'
        )
        self.assertEqual(
            account.document_spec['supported_document_types'],
            [u'passport', u'id-card', u'drivers-license']
        )
        self.assertEqual(
            account.document_spec['document_types_requiring_back'],
            [u'id-card', u'drivers-license']
        )


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

    def test_save(self):
        self.external_account.account_id = None
        with mock.patch(
                'stripe.Account.create_external_account', return_value=self.connect_account
        ) as create:
            with mock.patch(
                    'stripe.Account.retrieve', return_value=self.connect_account
            ):
                self.external_account.create('some-token')
                create.assert_called_with(
                    self.check.account_id,
                    external_account='some-token',
                )

                self.assertEqual(self.check.account.id, self.connect_account.id)

                self.assertEqual(
                    self.check.account_id,
                    self.connect_account.id
                )

    def test_save_already_created(self):
        self.assertRaises(
            ProgrammingError,
            self.external_account.create,
            'other-token'
        )

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
