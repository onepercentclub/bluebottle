import datetime
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
        created = datetime.datetime(2019, 1, 13, 23, 25, 0)
        orders = OrderFactory.create_batch(7, created=created)
        for order in orders:
            DonationFactory.create(project=self.project, order=order)
            order_payment = OrderPaymentFactory(order=order)
            payment = PaymentFactory(order_payment=order_payment)
            payment.status = 'settled'
            payment.save()
        created = datetime.datetime(2019, 1, 1, 3, 25, 0)
        orders = OrderFactory.create_batch(3, created=created)
        for order in orders:
            DonationFactory.create(project=self.project, order=order)
            order_payment = OrderPaymentFactory(order=order)
            payment = PaymentFactory(order_payment=order_payment)
            payment.status = 'unknown'
            payment.save()

    def test_export(self):

        call_command('export_donations',
                     '--start', '2019-01-01',
                     '--end', '2019-01-31',
                     '--file', 'temp.json')
        with open('temp.json') as json_data:
            data = json.load(json_data)
            self.assertEqual(len(data), 10)
            self.assertEqual(data[0]['donations'][0]['project_id'], self.project.id)
