from bluebottle.orders.models import Order

from bluebottle.payments.exception import PaymentException
from mock import patch
from moneyed import Money

from django.core.management import call_command
from django.test.utils import override_settings
from django.core import mail

from bluebottle.recurring_donations.models import MonthlyOrder, MonthlyBatch
from bluebottle.recurring_donations.tests.model_factory import \
    MonthlyDonorFactory, MonthlyDonorProjectFactory
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.projects.models import Project
from bluebottle.clients.utils import LocalTenant
from bluebottle.recurring_donations import tasks
from bluebottle.utils.utils import StatusDefinition
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase


class mock_payment_service(object):

    def __init__(self, order_payment):
        self.order_payment = order_payment

    def start_payment(self):
        # Throw some errors
        op = self.order_payment
        if op.id % 2:
            raise PaymentException('The horror, the horror')
        else:
            op.started()
            op.settled()
            op.save()
        return True

    def check_payment_status(self):
        pass


@override_settings(SEND_WELCOME_MAIL=False)
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
        # Top 3 after this should be projects 3, 4, 0
        order = OrderFactory()
        DonationFactory(order=order, project=self.projects[3], amount=10)
        DonationFactory(order=order, project=self.projects[3], amount=100)
        DonationFactory(order=order, project=self.projects[3], amount=20)

        DonationFactory(order=order, project=self.projects[4], amount=10)
        DonationFactory(order=order, project=self.projects[4], amount=70)

        DonationFactory(order=order, project=self.projects[0], amount=10)

        order.locked()
        order.save()
        order.success()
        order.save()

        # Since we force the transitions update_amounts isn't triggered by
        # signal, so we run it manually here.
        for project in self.projects:
            project.update_amounts()

        self.user1 = BlueBottleUserFactory.create()
        self.user2 = BlueBottleUserFactory.create()

        # Create a monthly donor with a preferred project
        self.monthly_donor1 = MonthlyDonorFactory(user=self.user1, amount=25)
        self.monthly_donor1_project = MonthlyDonorProjectFactory(
            donor=self.monthly_donor1, project=self.projects[0])

        # Create a monthly donor without preferred projects
        self.monthly_donor2 = MonthlyDonorFactory(user=self.user2, amount=100)
        Project.update_popularity()

    @patch('bluebottle.recurring_donations.tasks.PaymentService', mock_payment_service)
    def test_prepare_and_process(self):
        call_command('process_monthly_donations', prepare=True, tenant='test')

        # Now check that we have 2 prepared donations.
        self.assertEqual(MonthlyOrder.objects.count(), 2)

        # Check first monthly order
        monthly_order = MonthlyOrder.objects.get(user=self.user1)

        # Should have one donation
        self.assertEqual(monthly_order.donations.count(), 1)

        # Donation should have amount 25 and go to first project
        self.assertEqual(monthly_order.donations.all()[0].amount, Money(25, 'EUR'))
        self.assertEqual(monthly_order.donations.all()[0].project,
                         self.projects[0])

        # Check second monthly order
        # Should have 3 donations
        monthly_donations = MonthlyOrder.objects.get(user=self.user2).donations.all()
        self.assertEqual(len(monthly_donations), 3)

        self.assertEqual(monthly_donations[0].amount, Money(33.33, 'EUR'))
        self.assertEqual(monthly_donations[0].project, self.projects[3])

        self.assertEqual(monthly_donations[1].amount, Money(33.33, 'EUR'))
        self.assertEqual(monthly_donations[1].project, self.projects[4])

        self.assertEqual(monthly_donations[2].amount, Money(33.34, 'EUR'))
        self.assertEqual(monthly_donations[2].project, self.projects[0])

        batch = MonthlyBatch.objects.all()[0]
        self.assertEqual(batch.orders.count(), 2)

        # There should be one order for the earlier donations
        self.assertEqual(Order.objects.count(), 1)
        call_command('process_monthly_donations', process=True, tenant='test')

        # One of the monthly orders should have succeeded according to the mocked payment service
        self.assertEqual(Order.objects.filter(order_type='recurring',
                                              status__in=[StatusDefinition.SUCCESS]).count(), 1)

        # One of the monthly orders has failed based on the setup of the mock payment service
        self.assertEqual(Order.objects.filter(order_type='recurring',
                                              status__in=[StatusDefinition.FAILED]).count(), 1)

    @patch.object(tasks, 'PAYMENT_METHOD', 'mock')
    def test_email(self):
        with patch.object(LocalTenant, '__new__'):
            # Clear the outbox before running monthly donations
            del mail.outbox[:]
            call_command('process_monthly_donations', tenant='test', process=True, prepare=True)
            self.assertEquals(len(mail.outbox), 2)
