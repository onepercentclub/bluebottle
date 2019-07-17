from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.funding.transitions import PaymentTransitions
from bluebottle.funding_lipisha.tests.factories import LipishaPaymentFactory, LipishaPaymentProviderFactory

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class LipishaPaymentTestCase(BluebottleTestCase):
    def setUp(self):
        super(LipishaPaymentTestCase, self).setUp()
        LipishaPaymentProviderFactory.create()

        self.initiative = InitiativeFactory.create()

        self.initiative.transitions.submit()
        self.initiative.transitions.approve()

        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonationFactory.create(activity=self.funding)

    def test_create(self):
        payment = LipishaPaymentFactory(donation=self.donation)
        payment.save()

        self.assertEqual(payment.status, PaymentTransitions.values.new)
