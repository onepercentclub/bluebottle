from django.test.utils import override_settings

from bluebottle.payments_interswitch.adapters import InterswitchPaymentAdapter
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.utils import BluebottleTestCase

@override_settings()
class InterswitchPaymentAdapterTestCase(BluebottleTestCase):

    def setUp(self):
        self.order_payment = OrderPaymentFactory.create()
        self.adapter = InterswitchPaymentAdapter(self.order_payment)

    def test_create_payment(self):
        payment = self.adapter.create_payment()
