from django.core import mail
from djmoney.money import Money

from bluebottle.funding.tests.factories import FundingFactory, DonorFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.wallposts.models import SystemWallpost


class TestDonationSignalsTestCase(BluebottleTestCase):

    def setUp(self):
        super(TestDonationSignalsTestCase, self).setUp()
        self.user = BlueBottleUserFactory.create()
        self.funding = FundingFactory.create(target=Money(5000, 'EUR'), status='open')

    def test_successful_donation(self):
        """
        Test that a SystemWallpost is created for the project wall
        when a user does a successful donation
        """
        self.donation = DonorFactory(
            amount=Money(35, 'EUR'),
            user=self.user,
            activity=self.funding
        )
        self.donation.states.succeed()
        self.donation.save()
        self.assertEqual(SystemWallpost.objects.count(), 1)
        self.assertEqual(SystemWallpost.objects.all()[0].content_object, self.funding)
        self.assertEqual(len(mail.outbox), 2)

    def test_successful_donation_only_once(self):
        """
        Test that a SystemWallpost is created for the project wall
        when a user does a successful donation
        """
        self.donation = DonorFactory(
            amount=Money(35, 'EUR'),
            user=self.user,
            activity=self.funding
        )
        self.donation.states.succeed(save=True)
        self.assertEqual(SystemWallpost.objects.count(), 1)
        self.assertEqual(SystemWallpost.objects.first().content_object, self.funding)
        self.donation.states.fail(save=True)
        self.donation.states.succeed(save=True)
        self.assertEqual(SystemWallpost.objects.count(), 1)

    def test_successfull_anonymous_donation(self):
        """
        Test that a SystemWallpost is created without an author when a donation is anonymous
        """
        self.assertEqual(SystemWallpost.objects.count(), 0)
        self.donation = DonorFactory(
            amount=Money(35, 'EUR'),
            user=None,
            activity=self.funding
        )
        self.donation.states.succeed()
        self.donation.save()

        self.assertEqual(SystemWallpost.objects.count(), 1)
        self.assertEqual(SystemWallpost.objects.all()[0].author, None)
