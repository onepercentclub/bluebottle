from django.core import mail
from djmoney.money import Money

from bluebottle.funding.tests.factories import FundingFactory, DonorFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class TestDonationSignalsTestCase(BluebottleTestCase):

    def setUp(self):
        super(TestDonationSignalsTestCase, self).setUp()
        self.user = BlueBottleUserFactory.create()
        self.funding = FundingFactory.create(target=Money(5000, 'EUR'), status='open')

    def test_successful_donation(self):
        self.donation = DonorFactory(
            amount=Money(35, 'EUR'),
            user=self.user,
            activity=self.funding
        )
        self.donation.states.succeed(save=True)
        self.assertEqual(len(mail.outbox), 2)
