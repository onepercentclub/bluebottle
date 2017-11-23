import os

from django.test.utils import override_settings
from django.core import mail
from django.conf import settings
from django.utils.translation import ugettext as _

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory


@override_settings(
    MULTI_TENANT_DIR=os.path.join(settings.PROJECT_ROOT, 'bluebottle', 'test',
                                  'properties'))
class TestPaymentEmails(BluebottleTestCase):
    def setUp(self):
        super(TestPaymentEmails, self).setUp()

        self.init_projects()

        campaign_status = ProjectPhase.objects.get(slug='campaign')
        self.project = ProjectFactory.create(status=campaign_status)

        self.donor = BlueBottleUserFactory.create(first_name='projectdonor')
        self.order = OrderFactory.create(
            user=self.donor,
        )

        self.donation = DonationFactory.create(
            order=self.order,
            project=self.project,
            fundraiser=None
        )

        self.order_payment = OrderPaymentFactory.create(order=self.order)

        self.order_payment.started()
        self.order_payment.authorized()
        self.order_payment.save()

    def test_refund_mail(self):
        # Clear the email folder
        mail.outbox = []

        # Refund the order payment
        self.order_payment.refunded()
        self.order.save()

        self.assertEqual(len(mail.outbox), 1)

        # Test email to donor
        donor_mail = mail.outbox[0]
        self.assertEqual(donor_mail.to[0], self.donor.email)
        self.assertEqual(donor_mail.subject, _('Donation Refund'))
        self.assertTrue(self.project.title in donor_mail.body)
        self.assertTrue('admin@example.com' in donor_mail.body)

    def test_refund_mail_anonymous(self):
        self.order.user = None
        self.order.save()

        # Clear the email folder
        mail.outbox = []

        # Refund the order payment
        self.order_payment.refunded()
        self.order.save()

        self.assertEqual(len(mail.outbox), 0)
