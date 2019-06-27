import mock

from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.funding_vitepay.models import VitepayPayment
from bluebottle.funding_vitepay.tests.factories import VitepayPaymentFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class VitepayPaymentTestCase(BluebottleTestCase):
    def setUp(self):
        super(VitepayPaymentTestCase, self).setUp()
        self.initiative = InitiativeFactory.create()

        self.initiative.submit()
        self.initiative.approve()

        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonationFactory.create(activity=self.funding)

    def test_create(self):
        payment = VitepayPaymentFactory(donation=self.donation)

        with mock.patch('stripe.PaymentIntent.create', return_value=self.payment_intent):
            payment.save()

        self.assertEqual(payment.status, VitepayPayment.Status.new)
