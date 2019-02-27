from bluebottle.test.factory_models.geo import CountryFactory

from bunch import bunchify

from django.test.utils import override_settings

from mock import patch, Mock

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.payments_docdata.adapters import DocdataPaymentAdapter
from bluebottle.payments_docdata.exceptions import DocdataPaymentStatusException
from bluebottle.payments_docdata.tests.factory_models import DocdataPaymentFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory, OrderFactory
from bluebottle.test.utils import BluebottleTestCase, FsmTestMixin


# Mock create_payment so we don't need to call the external docdata service
def fake_create_payment(self):
    payment = self.MODEL_CLASS(order_payment=self.order_payment,
                               **self.order_payment.integration_data)
    payment.total_gross_amount = self.order_payment.amount
    payment.payment_cluster_key = 'abc123'
    payment.payment_cluster_id = 'abc123'
    payment.save()

    return payment


@override_settings(DEFAULT_COUNTRY_CODE='BG')
class PaymentsDocdataAdapterTestCase(BluebottleTestCase, FsmTestMixin):
    def setUp(self):
        super(PaymentsDocdataAdapterTestCase, self).setUp()
        patch.object(DocdataPaymentAdapter, 'create_payment', fake_create_payment)

    @patch('bluebottle.payments_docdata.adapters.gateway.DocdataClient')
    def test_payment_country_without_profile(self, mock_client):
        # For anonymous donations the default from settings should be used.
        instance = mock_client.return_value
        instance.create.return_value = {'order_key': 123, 'order_id': 123}
        order_payment = OrderPaymentFactory(payment_method='docdataCreditcard',
                                            integration_data={'default_pm': 'mastercard'})
        self.adapter = DocdataPaymentAdapter(order_payment=order_payment)
        payment = self.adapter.payment
        self.assertEqual(payment.country, 'BG')

    @patch('bluebottle.payments_docdata.adapters.gateway.DocdataClient')
    def test_payment_country_with_profile_without_country(self, mock_client):
        # If no country specified in profile the default from settings should be used
        instance = mock_client.return_value
        instance.create.return_value = {'order_key': 123, 'order_id': 123}
        user = BlueBottleUserFactory()
        order_payment = OrderPaymentFactory(user=user,
                                            payment_method='docdataCreditcard',
                                            integration_data={'default_pm': 'mastercard'})
        order_payment.order.user = user
        self.adapter = DocdataPaymentAdapter(order_payment=order_payment)
        payment = self.adapter.payment
        self.assertEqual(payment.country, 'BG')

    @patch('bluebottle.payments_docdata.adapters.gateway.DocdataClient')
    def test_payment_country_without_user(self, mock_client):
        # For donations without users some defaults should be used
        instance = mock_client.return_value
        instance.create.return_value = {'order_key': 123, 'order_id': 123}
        order_payment = OrderPaymentFactory(payment_method='docdataCreditcard',
                                            integration_data={'default_pm': 'ideal'})
        order_payment.order.user = None
        order_payment.order.save()
        self.adapter = DocdataPaymentAdapter(order_payment=order_payment)
        payment = self.adapter.payment
        self.assertEqual(payment.first_name, 'Nomen')
        self.assertEqual(payment.last_name, 'Nescio')


class DocdataClientMock():
    class service():
        @staticmethod
        def status(*args, **kwargs):
            return bunchify({
                'statusSuccess': {
                    'report': {
                        'payment': [
                            bunchify({'id': 'test-id', 'authorization': {}}),
                            bunchify({'id': 'test-id-2', 'authorization': {'refund': {}}})
                        ]
                    }
                }
            })

        def refund(*args, **kwargs):
            pass

    class factory:
        @staticmethod
        def create(ns):
            return Mock()


@override_settings(
    DOCDATA_FEES={'payment_methods': {'ideal': 0.20}, 'transaction': 0.20}
)
@patch('bluebottle.payments_docdata.gateway.Client', return_value=DocdataClientMock())
class PaymentsDocdataAdapterRefundTestCase(BluebottleTestCase, FsmTestMixin):
    def setUp(self):
        super(PaymentsDocdataAdapterRefundTestCase, self).setUp()
        self.order_payment = OrderPaymentFactory.create(
            status='started',
            payment_method='docdataIdeal',
            integration_data={'default_pm': 'ideal'},
            order=OrderFactory.create(status='locked')
        )
        DocdataPaymentFactory.create(
            order_payment=self.order_payment,
            payment_cluster_key='123-4',
            default_pm='ideal',
            total_gross_amount=100,
            status='settled'
        )
        self.adapter = DocdataPaymentAdapter(self.order_payment)

    def test_refund(self, mock_client):
        refund_reply = bunchify({
            'refundSuccess': True
        })

        with patch.object(
            DocdataClientMock.service, 'refund', return_value=refund_reply
        ) as refund_mock:
            self.adapter.refund_payment()
            self.assertEqual(refund_mock.call_count, 1)
            self.assertEqual(
                refund_mock.call_args[0][1], 'test-id'
            )

    def test_refund_failure(self, mock_client):
        refund_reply = bunchify({
            'refundError': {'error': {'_code': 'some code', 'value': 'some value'}}
        })

        with patch.object(
            DocdataClientMock.service, 'refund', return_value=refund_reply
        ):
            with self.assertRaises(DocdataPaymentStatusException):
                self.adapter.refund_payment()
