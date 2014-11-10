from bluebottle.test.utils import BluebottleTestCase
from django.core import mail
from django.test import TestCase

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.fundraisers import FundRaiserFactory
from bluebottle.test.factory_models.donations import DonationFactory

from bluebottle.utils.model_dispatcher import get_donation_model, get_order_model

DONATION_MODEL = get_donation_model()
ORDER_MODEL = get_order_model()


class DonationEmailTests(BluebottleTestCase):
    """ Tests for tasks: sending e-mails on certain status changes. """

    def setUp(self):
        super(DonationEmailTests, self).setUp()
        self.user = BlueBottleUserFactory.create(first_name='user')
        self.fund_owner = BlueBottleUserFactory.create(first_name='fundraiser')

        self.some_project = ProjectFactory.create()

        self.fundraiser_project = FundRaiserFactory.create(
            owner=self.fund_owner,
            project=self.some_project,
        )

        self.order = OrderFactory.create(
            user=self.user,
        )

        self.donation = DonationFactory.create(
            order=self.order,
            fundraiser=self.fundraiser_project
        )

    def test_mail_new_donation_after_successful(self):
        """ Testing if the e-mail is sent """

        # cleaning outbox
        mail.outbox = []

        self.order.locked()
        self.order.succeeded()

        self.assertEqual(len(mail.outbox), 1, 'it\'s actually {0}'.format(len(mail.outbox)))
        m = mail.outbox.pop(0)
        self.assertEqual(m.subject, 'You received a new donation')

