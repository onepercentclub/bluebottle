from django.core import mail
from django.utils.translation import ugettext as _

from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.fundraisers import FundraiserFactory
from bluebottle.test.factory_models.donations import DonationFactory

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.utils import BluebottleTestCase


class TestDonationEmails(BluebottleTestCase):
    """ Tests for tasks: sending e-mails on certain status changes. """

    def setUp(self):
        super(TestDonationEmails, self).setUp()
        self.init_projects()
        
        self.user = BlueBottleUserFactory.create(first_name='user')

        self.project_owner = BlueBottleUserFactory.create(first_name='projectowner')
        campaign_status = ProjectPhase.objects.get(slug='campaign')
        self.some_project = ProjectFactory.create(owner=self.project_owner, status=campaign_status)

        self.order = OrderFactory.create(
            user=self.user,
        )

        self.recurring_order = OrderFactory.create(
            user=self.user,
            order_type="recurring"
        )

        self.donation = DonationFactory.create(
            order=self.order,
            project=self.some_project,
            fundraiser=None
        )

        self.recurring_donation = DonationFactory.create(
            order=self.recurring_order,
            project=self.some_project,
            fundraiser=None
        )

        self.fund_order = OrderFactory.create(
            user=self.user,
        )

        self.fund_project = ProjectFactory.create(owner=self.project_owner, status=campaign_status)

        self.fund_owner = BlueBottleUserFactory.create(first_name='fundraiser')

        self.fundraiser_project = FundraiserFactory.create(
            owner=self.fund_owner,
            project=self.fund_project,
        )

        self.fund_donation = DonationFactory.create(
            order=self.fund_order,
            project=self.fund_project,
            fundraiser=self.fundraiser_project
        )

    def test_mail_project_owner_successful_donation(self):
        """ Test that an email is sent to the project owner after a succesful donation """
        # Clear the email folder
        mail.outbox = []

        # Prepare the order
        self.order.locked()
        self.order.succeeded()

        # No fundraiser so one mail should be sent: one to the owner
        self.assertEqual(len(mail.outbox), 1)

        # Test email to owner
        self.assertEqual(mail.outbox[0].to[0], self.project_owner.email)
        self.assertEqual(mail.outbox[0].subject, _('You received a new donation'))
        self.assertTrue("EUR {0}".format(self.donation.amount) in mail.outbox[0].body)


    def test_mail_no_mail_not_one_off(self):
        """ Test that no email is sent when its not a one-off donation"""
        # Clear the email folder
        mail.outbox = []

        # Prepare the order
        self.recurring_order.locked()
        self.recurring_order.succeeded()

        # No mail because its not a one-off donation
        self.assertEqual(len(mail.outbox), 0)


    def test_mail_fundraiser_successful_donation(self):
        "Test that an email is sent to the fundraiser after a succesful donation"

        # Clear the email folder
        mail.outbox = []

        # Prepare the order
        self.fund_order.locked()
        self.fund_order.succeeded()

        # With fundraiser so two mails should be sent: one to the owner and one to fundraiser.
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to[0], self.fund_owner.email)
        self.assertEqual(mail.outbox[0].subject, _('You received a new donation'))
        self.assertTrue("EUR {0}".format(self.fund_donation.amount) in mail.outbox[0].body)






