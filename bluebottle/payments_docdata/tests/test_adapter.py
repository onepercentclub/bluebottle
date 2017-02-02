from bluebottle.test.factory_models.geo import CountryFactory

from django.test.utils import override_settings

from mock import patch

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.payments_docdata.adapters import DocdataPaymentAdapter
from bluebottle.test.factory_models.payments import OrderPaymentFactory
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
    def test_payment_country_with_profile(self, mock_client):
        # When a country is set in profile, that should be used.
        instance = mock_client.return_value
        instance.create.return_value = {'order_key': 123, 'order_id': 123}
        user = BlueBottleUserFactory()
        user.address.country = CountryFactory(name='Netherlands', alpha2_code='NL')
        order_payment = OrderPaymentFactory(user=user,
                                            payment_method='docdataCreditcard',
                                            integration_data={'default_pm': 'mastercard'})
        order_payment.order.user = user
        self.adapter = DocdataPaymentAdapter(order_payment=order_payment)
        payment = self.adapter.payment
        self.assertEqual(payment.country, 'NL')

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
    def test_ideal_payment_country_with_profile(self, mock_client):
        # Even a yankees should get NL for country when selecting iDEAL.
        instance = mock_client.return_value
        instance.create.return_value = {'order_key': 123, 'order_id': 123}
        user = BlueBottleUserFactory()
        user.address.country = CountryFactory(name='Merica', alpha2_code='US')
        order_payment = OrderPaymentFactory(user=user,
                                            payment_method='docdataIdeal',
                                            integration_data={'default_pm': 'ideal'})
        order_payment.order.user = user
        self.adapter = DocdataPaymentAdapter(order_payment=order_payment)
        payment = self.adapter.payment
        self.assertEqual(payment.country, 'NL')
