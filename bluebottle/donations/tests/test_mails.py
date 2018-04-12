from django.contrib.auth.models import Group, Permission
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

        self.user = BlueBottleUserFactory.create(first_name='user', last_name='userson')
        self.user.address.line1 = "'s Gravenhekje 1A"
        self.user.address.city = "Mokum A"
        self.user.save()

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

        self.fund_project = ProjectFactory.create(owner=self.project_owner,
                                                  status=campaign_status)

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
        """ Test that an email is sent to the project owner after a successful donation """
        # Clear the email folder
        mail.outbox = []

        # Prepare the order
        self.order.locked()
        self.order.save()
        self.order.success()
        self.order.save()

        # No fundraiser so 2 mails should be sent: one to the owner, and one to the donor
        self.assertEqual(len(mail.outbox), 2)

        # Test email to owner
        self.assertEqual(mail.outbox[0].to[0], self.project_owner.email)
        self.assertEqual(mail.outbox[0].subject, _('You received a new donation'))

        # Test that last name is found in the email
        self.assertTrue(self.user.last_name in mail.outbox[0].body)
        # self.assertTrue(self.user.address.line1 in mail.outbox[0].body)
        # self.assertTrue(self.user.address.city in mail.outbox[0].body)
        self.assertTrue("{0}".format(self.donation.amount.amount) in mail.outbox[0].body)

    def test_mail_external_project_owner_successful_donation(self):
        """
        Test that an email is sent to an external project owner after a successful donation,
        make sure that only first name is shared.
        """
        # Clear the email folder
        mail.outbox = []

        auth = Group.objects.get(name='Authenticated')
        auth.permissions.remove(
            Permission.objects.get(codename='api_read_full_member')
        )

        # Prepare the order
        self.order.locked()
        self.order.save()
        self.order.success()
        self.order.save()

        # No fundraiser so 2 mails should be sent: one to the owner, and one to the donor
        self.assertEqual(len(mail.outbox), 2)

        # Test email to owner
        self.assertEqual(mail.outbox[0].to[0], self.project_owner.email)
        self.assertEqual(mail.outbox[0].subject, _('You received a new donation'))

        # Test that last name is *not* found in the email
        self.assertTrue(self.user.first_name in mail.outbox[0].body)
        self.assertFalse(self.user.last_name in mail.outbox[0].body)
        self.assertFalse(self.user.address.line1 in mail.outbox[0].body)

    def test_mail_donor_successful_donation(self):
        """ Test that an email is sent to the donor after a succesful donation """
        # Clear the email folder
        mail.outbox = []

        # Prepare the order
        self.order.locked()
        self.order.save()
        self.order.success()
        self.order.save()

        # No fundraiser so 2 mails should be sent: one to the owner, and one to the donor
        self.assertEqual(len(mail.outbox), 2)

        # Test email to donor
        self.assertEqual(mail.outbox[1].to[0], self.user.email)
        self.assertEqual(mail.outbox[1].subject, _('Thanks for your donation'))

        body = mail.outbox[1].body

        self.assertTrue(
            "{0}".format(self.donation.amount.amount) in body
        )
        self.assertTrue(
            "Thanks {0}".format(self.user.first_name) in body
        )
        self.assertTrue(
            self.donation.project.owner.full_name in body
        )
        self.assertTrue(
            self.donation.project.organization.name in body
        )

    def test_mail_no_mail_not_one_off(self):
        """ Test that no email is sent when its not a one-off donation"""
        # Clear the email folder
        mail.outbox = []

        # Prepare the order
        self.recurring_order.locked()
        self.recurring_order.save()
        self.recurring_order.success()
        self.recurring_order.save()

        # No mail because its not a one-off donation
        self.assertEqual(len(mail.outbox), 0)

    def test_mail_fundraiser_successful_donation(self):
        "Test that an email is sent to the fundraiser after a succesful donation"

        # Clear the email folder
        mail.outbox = []

        # Prepare the order
        self.fund_order.locked()
        self.fund_order.save()
        self.fund_order.success()
        self.fund_order.save()

        # With fundraiser so 3 mails should be sent: one to the owner, one to the donor and one to fundraiser.
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(mail.outbox[0].to[0], self.fund_owner.email)
        self.assertEqual(mail.outbox[0].subject,
                         _('You received a new donation'))
        self.assertTrue(
            "{0}".format(self.fund_donation.amount.amount) in mail.outbox[0].body)
