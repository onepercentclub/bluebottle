import mock

from django.contrib.admin.sites import AdminSite
from django.test.client import RequestFactory

from bluebottle.payments.admin import OrderPaymentAdmin
from bluebottle.payments.models import OrderPayment
from bluebottle.payments_docdata.adapters import DocdataPaymentAdapter
from bluebottle.payments_docdata.tests.factory_models import DocdataPaymentFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.utils import BluebottleTestCase, override_settings


factory = RequestFactory()


class MockRequest:
    pass


class MockUser:
    def __init__(self, perms=None):
        self.perms = perms or []

    def has_perm(self, perm):
        return perm in self.perms


@override_settings(ENABLE_REFUNDS=True)
class TestOrderPaymentAdmin(BluebottleTestCase):
    def setUp(self):
        super(TestOrderPaymentAdmin, self).setUp()
        self.site = AdminSite()
        self.request_factory = RequestFactory()

        self.order_payment_admin = OrderPaymentAdmin(OrderPayment, self.site)
        self.order_payment = OrderPaymentFactory.create(
            payment_method='docdataIdeal',
            integration_data={'default_pm': 'ideal'},
        )
        DocdataPaymentFactory.create(
            order_payment=self.order_payment,
            payment_cluster_key='123-4',
            default_pm='ideal',
            total_gross_amount=100
        )

    def test_refund(self):
        request = self.request_factory.post('/')
        request.user = MockUser(['payments.refund_orderpayment'])

        with mock.patch.object(self.order_payment_admin, 'message_user') as message_mock:
            with mock.patch.object(DocdataPaymentAdapter, 'refund_payment') as refund_mock:
                response = self.order_payment_admin.refund(request, self.order_payment.pk)

                self.assertEqual(response.status_code, 302)
                message_mock.assert_called_with(
                    request,
                    'Refund is requested. It may take a while for this to be visble here'
                )
                refund_mock.assert_called()

    def test_refund_forbidden(self):
        request = self.request_factory.post('/')
        request.user = MockUser([])

        with mock.patch.object(self.order_payment_admin, 'message_user') as message_mock:
            with mock.patch.object(DocdataPaymentAdapter, 'refund_payment') as refund_mock:
                response = self.order_payment_admin.refund(request, self.order_payment.pk)

                self.assertEqual(response.status_code, 403)
                message_mock.assert_not_called()
                refund_mock.assert_not_called()

    @override_settings(ENABLE_REFUNDS=False)
    def test_refund_disabled(self):
        request = self.request_factory.post('/')
        request.user = MockUser(['payments.refund_orderpayment'])

        with mock.patch.object(self.order_payment_admin, 'message_user') as message_mock:
            with mock.patch.object(DocdataPaymentAdapter, 'refund_payment') as refund_mock:
                response = self.order_payment_admin.refund(request, self.order_payment.pk)

                self.assertEqual(response.status_code, 403)
                message_mock.assert_not_called()
                refund_mock.assert_not_called()
