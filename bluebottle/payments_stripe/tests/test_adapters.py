from mock import patch
import stripe

from django.test.utils import override_settings
from moneyed import Money

from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.factory_models.payouts import StripePayoutAccountFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.payments_stripe.adapters import StripePaymentAdapter


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
        payout_account = StripePayoutAccountFactory.create()
        self.project = ProjectFactory.create(payout_account=payout_account)
        order = OrderFactory.create()
        DonationFactory.create(project=self.project, order=order)
        self.order_payment = OrderPaymentFactory.create(
            payment_method='stripeCreditcard',
            integration_data={'chargeable': False, 'source_token': 'some token'},
            order=order,
            amount=100
        )

    def test_payment_is_created(self):
        adapter = StripePaymentAdapter(self.order_payment)
        self.assertTrue(adapter.payment.pk)
        self.assertEqual(adapter.payment.source_token, 'some token')
        self.assertEqual(adapter.payment.status, 'started')
        self.assertEqual(adapter.payment.method_name, 'Creditcard')

    def test_payment_is_created_and_charged(self):
        self.order_payment.card_data['chargeable'] = True
        charge = stripe.Charge('some charge token')
        charge.update({'status': 'succeeded', 'refunded': False})
        with patch('stripe.Charge.create', return_value=charge):
            adapter = StripePaymentAdapter(self.order_payment)
            self.assertTrue(adapter.payment.pk)
            self.assertEqual(adapter.payment.charge_token, 'some charge token')
            self.assertEqual(adapter.payment.status, 'settled')

    def test_payment_charged(self):
        charge = stripe.Charge('some charge token')
        charge.update({'status': 'succeeded', 'refunded': False})

        adapter = StripePaymentAdapter(self.order_payment)
        with patch('stripe.Charge.create', return_value=charge) as create:
            adapter.charge()

            self.assertTrue(adapter.payment.pk)
            self.assertEqual(adapter.payment.charge_token, 'some charge token')
            self.assertEqual(adapter.payment.status, 'settled')

            call_args = create.call_args[1]
            self.assertEqual(call_args['source'], self.order_payment.payment.source_token)
            self.assertEqual(call_args['metadata']['tenant_name'], 'test')
            self.assertEqual(call_args['metadata']['tenant_domain'], 'testserver')
            self.assertEqual(call_args['metadata']['project_slug'], self.project.slug)
            self.assertEqual(call_args['metadata']['project_title'], self.project.title)

    def test_check_payment_status(self):
        adapter = StripePaymentAdapter(self.order_payment)
        adapter.check_payment_status()
        self.assertEqual(adapter.payment.status, 'started')

    def test_check_payment_status_charged(self):
        charge = stripe.Charge('some charge token')
        charge.update({
            'status': 'succeeded',
            'transfer': 'tr_01',
            'refunded': False
        })
        transfer = stripe.Transfer('some charge token')
        transfer.update({
            'id': 'tr_01',
            'amount': 1210,
            'currency': 'usd'
        })

        adapter = StripePaymentAdapter(self.order_payment)
        self.order_payment.payment.charge_token = 'some charge token'
        with patch('stripe.Charge.retrieve', return_value=charge):
            with patch('stripe.Transfer.retrieve', return_value=transfer):
                adapter.check_payment_status()
                self.assertTrue(adapter.payment.pk)
                self.assertEqual(adapter.payment.status, 'settled')
                # Make sure payment/donation have an updated payout_amount
                self.assertEqual(adapter.payment.payout_amount, 1210)
                donation = self.order_payment.order.donations.first()
                self.assertEqual(donation.payout_amount, Money(12.10, 'USD'))

    def test_check_payment_status_refunded(self):
        charge = stripe.Charge('some charge token')
        charge.update({
            'status': 'succeeded',
            'refunded': True,
            'transfer': 'tr00001'
        })
        transfer = stripe.Transfer('some charge token')
        transfer.update({
            'amount': 10000,
            'currency': 'eur'
        })

        adapter = StripePaymentAdapter(self.order_payment)
        adapter.payment.status = 'settled'
        adapter.payment.save()

        self.order_payment.payment.charge_token = 'some charge token'
        with patch('stripe.Charge.retrieve', return_value=charge):
            with patch('stripe.Transfer.retrieve', return_value=transfer):
                adapter.check_payment_status()
                self.assertTrue(adapter.payment.pk)
                self.assertEqual(adapter.payment.status, 'refunded')

    def test_refund(self):
        adapter = StripePaymentAdapter(self.order_payment)
        adapter.payment.status = 'settled'
        adapter.payment.charge_token = 'some token'
        adapter.payment.save()

        with patch('stripe.Refund.create') as create_refund:
            adapter.refund_payment()
            self.assertEqual(adapter.payment.status, 'refund_requested')
            create_refund.assert_called_with(
                charge=adapter.payment.charge_token,
                api_key=MERCHANT_ACCOUNTS[0]['secret_key']
            )
