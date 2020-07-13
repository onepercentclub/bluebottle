from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.funding.transitions import PaymentTransitions
from bluebottle.funding_telesom.models import TelesomPaymentProvider
from bluebottle.funding_telesom.tests.factories import TelesomPaymentFactory, TelesomPaymentProviderFactory

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class TelesomPaymentTestCase(BluebottleTestCase):
    def setUp(self):
        super(TelesomPaymentTestCase, self).setUp()
        TelesomPaymentProvider.objects.all().delete()
        TelesomPaymentProviderFactory.create()
        self.initiative = InitiativeFactory.create()

        self.initiative.transitions.submit()
        self.initiative.transitions.approve()

        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonationFactory.create(activity=self.funding)

    def test_create(self):
        payment = TelesomPaymentFactory(donation=self.donation)
        payment.save()

        self.assertEqual(payment.status, PaymentTransitions.values.new)
