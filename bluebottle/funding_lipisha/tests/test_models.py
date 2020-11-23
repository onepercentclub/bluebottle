from bluebottle.funding.tests.factories import FundingFactory, DonorFactory
from bluebottle.funding_lipisha.models import LipishaPaymentProvider
from bluebottle.funding_lipisha.tests.factories import LipishaPaymentFactory, LipishaPaymentProviderFactory

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class LipishaPaymentTestCase(BluebottleTestCase):
    def setUp(self):
        super(LipishaPaymentTestCase, self).setUp()
        LipishaPaymentProvider.objects.all().delete()
        LipishaPaymentProviderFactory.create()

        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonorFactory.create(activity=self.funding)

    def test_create(self):
        payment = LipishaPaymentFactory(donation=self.donation)
        payment.save()

        self.assertEqual(payment.status, 'new')
