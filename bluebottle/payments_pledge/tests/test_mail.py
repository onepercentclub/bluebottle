import logging

from django.core import mail
from django.test.utils import override_settings

from mock import patch

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory


@override_settings(SEND_WELCOME_MAIL=False)
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
        self.order = OrderFactory.create(user=self.user)
        self.donation = DonationFactory(amount=60, order=self.order, project=self.project, fundraiser=None)

    def test_project_owner_mail(self):
        self.order_payment = OrderPaymentFactory.create(order=self.order,
                                                        payment_method='pledgeStandard')
        self.order_payment.pledged()

        self.assertEquals(len(mail.outbox), 2)
        self.assertNotEquals(mail.outbox[0].body.find("You received a"), -1)

    def test_donator_mail(self):
        self.order_payment = OrderPaymentFactory.create(order=self.order,
                                                        payment_method='pledgeStandard')
        self.order_payment.pledged()

        self.assertEquals(len(mail.outbox), 2)
        body = mail.outbox[1].body
        self.assertNotEquals(body.find("Please transfer the amount of"), -1)
        self.assertNotEquals(body.find("Method Invoiced"), -1)
