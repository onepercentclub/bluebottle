from decimal import Decimal
from bluebottle.recurring_donations.models import MonthlyOrder
from bluebottle.recurring_donations.tests.model_factory import MonthlyDonorFactory, MonthlyDonorProjectFactory
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase
from django.core.management import call_command

class MonthlyDonationCommandsTest(BluebottleTestCase):

    def setUp(self):
        super(MonthlyDonationCommandsTest, self).setUp()

        self.init_projects()
        self.phase_campaign = ProjectPhase.objects.get(slug='campaign')
        self.country = CountryFactory()

        self.projects = []

        for amount in [500, 100, 1500, 300, 200]:
            self.projects.append(
                ProjectFactory.create(amount_asked=amount,
                                      status=self.phase_campaign))

        # Some donations to get the popularity going
        # Top 3 after this should be projects 4, 3, 0
        order = OrderFactory()
        DonationFactory(order=order, project=self.projects[3], amount=10)
        DonationFactory(order=order, project=self.projects[3], amount=100)
        DonationFactory(order=order, project=self.projects[3], amount=20)

        DonationFactory(order=order, project=self.projects[4], amount=10)
        DonationFactory(order=order, project=self.projects[4], amount=70)

        DonationFactory(order=order, project=self.projects[0], amount=10)

        order.locked()
        order.succeeded()

        # Since we force the transitions update_amounts isn't triggered by
        # signal, so we run it manually here.
        for project in self.projects:
            project.update_amounts()

        self.user1 = BlueBottleUserFactory.create()
        self.user2 = BlueBottleUserFactory.create()

    def test_prepare(self):
        # Create a monthly donor with a preferred project
        monthly_donor1 = MonthlyDonorFactory(user=self.user1, amount=25)
        monthly_donor1_project = MonthlyDonorProjectFactory(
            donor=monthly_donor1, project=self.projects[0])

        # Create a monthly donor without preferred projects
        monthly_donor2 = MonthlyDonorFactory(user=self.user2, amount=100)

        call_command('process_monthly_donations', prepare=True,
                     tenant='test')

        # Now check that we have 2 prepared donations.
        self.assertEqual(MonthlyOrder.objects.count(), 2)

        # Check first monthly order
        monthly_order = MonthlyOrder.objects.get(user=self.user1)

        # Should have one donation
        self.assertEqual(monthly_order.donations.count(), 1)
        
        # Donation should have amount 25 and go to first project
        self.assertEqual(monthly_order.donations.all()[0].amount, Decimal('25'))
        self.assertEqual(monthly_order.donations.all()[0].project, self.projects[0])

        # Check second monthly order
        # Should have 3 donations
        monthly_donations = MonthlyOrder.objects.get(user=self.user2).donations.all()
        self.assertEqual(len(monthly_donations), 3)

        self.assertEqual(monthly_donations[0].amount, Decimal('33.33'))
        self.assertEqual(monthly_donations[0].project, self.projects[3])

        self.assertEqual(monthly_donations[1].amount, Decimal('33.33'))
        self.assertEqual(monthly_donations[1].project, self.projects[4])

        self.assertEqual(monthly_donations[2].amount, Decimal('33.34'))
        self.assertEqual(monthly_donations[2].project, self.projects[0])
