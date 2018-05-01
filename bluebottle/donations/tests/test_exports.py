import json

from django.core.management import call_command

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory, PaymentFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase, SessionTestMixin


class TestDonationExport(BluebottleTestCase, SessionTestMixin):
    def setUp(self):
        super(TestDonationExport, self).setUp()
        self.project = ProjectFactory.create(amount_asked=5000)
        self.user = BlueBottleUserFactory.create()
        self.orders = OrderFactory.create_batch(7)
        for order in self.orders:
            DonationFactory.create(project=self.project, order=order)
            order_payment = OrderPaymentFactory(order=order)
            payment = PaymentFactory(order_payment=order_payment)
            payment.status = 'settled'
            payment.save()

    def test_export(self):
        call_command('export_donations', '--file', 'temp.json')
        with open('temp.json') as json_data:
            data = json.load(json_data)
            self.assertEqual(len(data), 7)
            self.assertEqual(data[0]['donations'][0]['project_id'], self.project.id)
