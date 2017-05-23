from mock import patch
from moneyed import Money

from django.test.utils import override_settings
from django.core import mail

from django_webtest import WebTestMixin
from tenant_schemas.urlresolvers import reverse

from bluebottle.recurring_donations.models import MonthlyOrder, MonthlyBatch
from bluebottle.recurring_donations.tests.model_factory import \
    MonthlyDonorFactory, MonthlyDonorProjectFactory
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.projects.models import Project
from bluebottle.recurring_donations import tasks
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase


@patch.object(tasks, 'PAYMENT_METHOD', 'mock')
@override_settings(SEND_WELCOME_MAIL=False)
class MonthlyDonationAdminTest(WebTestMixin, BluebottleTestCase):

    def setUp(self):
        super(MonthlyDonationAdminTest, self).setUp()

        self.app.extra_environ['HTTP_HOST'] = str(self.tenant.domain_url)
        self.superuser = BlueBottleUserFactory.create(is_staff=True, is_superuser=True)

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

    def test_prepare(self):
        del mail.outbox[:]
        admin_prepare_url = reverse('admin:recurring_donations_monthlybatch_prepare')
        prepare_page = self.app.get(admin_prepare_url, user=self.superuser)

        self.assertEqual(prepare_page.status_code, 302)

        # Now check that we have 1 prepared batch.
        self.assertEqual(MonthlyBatch.objects.count(), 1)
        batch = MonthlyBatch.objects.all()[0]
        self.assertEqual(batch.status, 'new')

        # Check that we get redirect to the monthly batch detail page
        admin_batch_url = reverse('admin:recurring_donations_monthlybatch_change', args=(batch.id,))
        self.assertRedirects(prepare_page, admin_batch_url)

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
        monthly_donations = MonthlyOrder.objects.get(
            user=self.user2).donations.all()
        self.assertEqual(len(monthly_donations), 3)

        self.assertEqual(monthly_donations[0].amount, Money(33.33, 'EUR'))
        self.assertEqual(monthly_donations[0].project, self.projects[3])

        self.assertEqual(monthly_donations[1].amount, Money(33.33, 'EUR'))
        self.assertEqual(monthly_donations[1].project, self.projects[4])

        self.assertEqual(monthly_donations[2].amount, Money(33.34, 'EUR'))
        self.assertEqual(monthly_donations[2].project, self.projects[0])

        # Now process it
        admin_prepare_url = reverse('admin:recurring_donations_monthlybatch_process', args=(batch.id,))
        prepare_page = self.app.get(admin_prepare_url, user=self.superuser)

        self.assertEqual(prepare_page.status_code, 302)
        self.assertRedirects(prepare_page, admin_batch_url)

        self.assertEquals(len(mail.outbox), 2)
        batch = MonthlyBatch.objects.all()[0]
        self.assertEqual(batch.status, 'done')
