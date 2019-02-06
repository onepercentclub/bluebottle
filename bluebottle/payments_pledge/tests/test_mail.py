import os

from django.core import mail
from django.test.utils import override_settings
from django.conf import settings

from bluebottle.test.factory_models.payouts import PlainPayoutAccountFactory, StripePayoutAccountFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory


@override_settings(
    SEND_WELCOME_MAIL=False,
    MULTI_TENANT_DIR=os.path.join(settings.PROJECT_ROOT, 'bluebottle', 'test',
                                  'properties'))
class TestPledgeMails(BluebottleTestCase):
    """
    Test the sending of email notifications when a Task' status changes
    """

    def setUp(self):
        super(TestPledgeMails, self).setUp()

        self.init_projects()

        self.user = BlueBottleUserFactory(can_pledge=True)
        self.project_owner = BlueBottleUserFactory(username='proj1_owner',
                                                   email='owner@proj1.nl', password='proj1')
        self.organization = OrganizationFactory.create(name='test_org', slug='test_org')

        self.project = ProjectFactory(owner=self.project_owner, organization=self.organization,
                                      title='Project 1', amount_needed=1111, amount_asked=1111)
        self.project.payout_account = PlainPayoutAccountFactory.create(
            account_number='1234567890',
            account_holder_name='Henk'
        )
        self.project.save()
        self.order = OrderFactory.create(user=self.user)
        self.donation = DonationFactory(amount=60, order=self.order,
                                        project=self.project, fundraiser=None)

        self.order_payment = OrderPaymentFactory.create(order=self.order,
                                                        payment_method='pledgeStandard')
        self.order_payment.pledged()
        self.order_payment.save()

    def test_platform_admin_mail(self):
        body = mail.outbox[2].body

        self.assertEquals(len(mail.outbox), 3)
        self.assertTrue("A project just received an invoiced donation" in body)
        self.assertTrue(self.user.full_name in body)

    def test_project_owner_mail(self):
        body = mail.outbox[0].body

        self.assertEquals(len(mail.outbox), 3)
        self.assertTrue("received an invoiced donation" in body)
        self.assertTrue(self.user.full_name in body)

        self.assertTrue('admin@example.com' in body, 'Email includes tenant admin address')

    def test_donator_mail(self):
        body = mail.outbox[1].body
        self.assertEquals(len(mail.outbox), 3)
        self.assertEqual(self.project.payout_account.account_number, '1234567890')
        self.assertTrue("Please transfer the amount of" in body)
        self.assertTrue(self.project.title in body)
        self.assertTrue("Invoiced" in body)


@override_settings(
    SEND_WELCOME_MAIL=False,
    MULTI_TENANT_DIR=os.path.join(settings.PROJECT_ROOT, 'bluebottle', 'test',
                                  'properties'))
class TestPledgeStripeMails(BluebottleTestCase):
    """
    Test the sending of email notifications when a Task' status changes
    """

    def setUp(self):
        super(TestPledgeStripeMails, self).setUp()

        self.init_projects()

        self.user = BlueBottleUserFactory(can_pledge=True)
        self.project_owner = BlueBottleUserFactory(username='proj1_owner',
                                                   email='owner@proj1.nl', password='proj1')
        self.organization = OrganizationFactory.create(name='test_org', slug='test_org')

        self.project = ProjectFactory(owner=self.project_owner, organization=self.organization,
                                      title='Project 1', amount_needed=1111, amount_asked=1111)
        self.project.payout_account = StripePayoutAccountFactory.create()
        self.project.save()
        self.order = OrderFactory.create(user=self.user)
        self.donation = DonationFactory(amount=60, order=self.order,
                                        project=self.project, fundraiser=None)

        self.order_payment = OrderPaymentFactory.create(order=self.order,
                                                        payment_method='pledgeStandard')
        self.order_payment.pledged()
        self.order_payment.save()

    def test_donator_mail(self):
        body = mail.outbox[1].body
        self.assertEquals(len(mail.outbox), 3)
        self.assertTrue("Please transfer the amount of" in body)
        self.assertTrue("Invoiced" in body)
