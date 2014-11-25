from django.core import mail
from django.test import TestCase
from django.utils.translation import ugettext as _

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.fundraisers import FundRaiserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.model_dispatcher import get_donation_model, get_order_model

DONATION_MODEL = get_donation_model()
ORDER_MODEL = get_order_model()


class TestDonationEmails(BluebottleTestCase):
    """ Tests for tasks: sending e-mails on certain status changes. """

    def setUp(self):
        super(TestDonationEmails, self).setUp()
        self.user = BlueBottleUserFactory.create(first_name='user')

        self.project_owner = BlueBottleUserFactory.create(first_name='projectowner')
        self.some_project = ProjectFactory.create(owner=self.project_owner)


        self.order = OrderFactory.create(
            user=self.user,
        )

        self.donation = DonationFactory.create(
            order=self.order,
            project=self.some_project,
            fundraiser=None
        )

    def test_mail_project_owner_and_supporter_successful_donation(self):
        """ Test that an email is sent to the project owner and project supporter after a succesful donation """
        # Clear the email folder
        mail.outbox = []

        # Prepare the order
        self.order.locked()
        self.order.succeeded()

        # No fundraiser so two mails should be sent: one to the owner and one to the supporter
        self.assertEqual(len(mail.outbox), 2)

        # Test email to owner
        self.assertEqual(mail.outbox[0].to[0], self.project_owner.email)
        self.assertEqual(mail.outbox[0].subject, _('You received a new donation'))

        # Test email to supporter
        self.assertEqual(mail.outbox[1].to[0], self.user.email)
        # TODO: Test the email content
        # self.assertEqual(mail.outbox[0].subject, _('You received a new donation'))


    def test_mail_fundraiser_successful_donation(self):
        "Test that an email is sent to the fundraiser after a succesful donation"

        # Clear the email folder
        mail.outbox = []

        # Prepare the order
        self.order.locked()
        self.order.succeeded()

        fund_owner = BlueBottleUserFactory.create(first_name='fundraiser')

        fundraiser_project = FundRaiserFactory.create(
            owner=fund_owner,
            project=self.some_project,
        )

        # Withfundraiser so three mails should be sent: one to the owner, one to the supporter, one to fundraiser
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(mail.outbox[2].to[0], fund_owner.email)



