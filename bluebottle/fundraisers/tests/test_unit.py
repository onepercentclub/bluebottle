from moneyed.classes import Money

from bluebottle.projects.models import ProjectPhase
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.fundraisers import FundraiserFactory
from bluebottle.utils.utils import StatusDefinition


class TestFundraiserAmountDonated(BluebottleTestCase):
    """
    Test that amount donated is calculated correctly
    """

    def setUp(self):
        super(TestFundraiserAmountDonated, self).setUp()

        self.init_projects()

        campaign = ProjectPhase.objects.get(slug="campaign")
        project = ProjectFactory.create(status=campaign)
        self.fundraiser = FundraiserFactory(project=project, amount=Money(1000, 'EUR'))

    def test_single_donation(self):
        DonationFactory.create(
            order=OrderFactory.create(status=StatusDefinition.SUCCESS),
            fundraiser=self.fundraiser,
            amount=Money(100, 'EUR'),
        )

        self.assertEqual(
            self.fundraiser.amount_donated,
            Money(100, 'EUR')
        )

    def test_single_donation_different_currency(self):
        DonationFactory.create(
            order=OrderFactory.create(status=StatusDefinition.SUCCESS),
            fundraiser=self.fundraiser,
            amount=Money(100, 'USD')
        )

        self.assertEqual(
            self.fundraiser.amount_donated,
            Money(150, 'EUR')
        )

    def test_multiple_donations(self):
        DonationFactory.create(
            order=OrderFactory.create(status=StatusDefinition.SUCCESS),
            fundraiser=self.fundraiser,
            amount=Money(100, 'USD')
        )
        DonationFactory.create(
            order=OrderFactory.create(status=StatusDefinition.SUCCESS),
            fundraiser=self.fundraiser,
            amount=Money(100, 'EUR')
        )

        self.assertEqual(
            self.fundraiser.amount_donated,
            Money(250, 'EUR')
        )
