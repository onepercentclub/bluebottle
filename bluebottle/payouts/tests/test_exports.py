import json

from bluebottle.test.factory_models.payouts import ProjectPayoutFactory
from django.core.management import call_command

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory, PaymentFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase, SessionTestMixin
from moneyed.classes import Money


class TestPayoutExport(BluebottleTestCase, SessionTestMixin):
    def setUp(self):
        super(TestPayoutExport, self).setUp()
        self.project = ProjectFactory.create(amount_asked=5000)
        self.user = BlueBottleUserFactory.create()
        self.orders = OrderFactory.create_batch(7)
        for order in self.orders:
            DonationFactory.create(project=self.project, order=order)
            order_payment = OrderPaymentFactory(order=order)
            payment = PaymentFactory(order_payment=order_payment)
            payment.status = 'settled'
            payment.save()
        self.payout = ProjectPayoutFactory(
            project=self.project,
            amount_payable=Money(125.00, 'EUR'),
            amount_raised=Money(175.0, 'EUR'),
            status='settled'
        )

    def test_export(self):
        call_command('export_payouts', '--file', 'temp.json')
        with open('temp.json') as json_data:
            data = json.load(json_data)
            self.assertEqual(len(data), 1)
            self.assertEqual(len(data[0]['donations']), 7)
            self.assertEqual(data[0]['amount_payable'], {'currency': 'EUR', 'amount': 125.00})
