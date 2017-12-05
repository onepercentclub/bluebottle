import os
from decimal import Decimal
from moneyed import Money

from django.test.utils import override_settings
from django.conf import settings
from django.utils import timezone

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.donations.models import Donation
from bluebottle.payouts.models import ProjectPayout
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.factory_models.payouts import ProjectPayoutFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.utils import StatusDefinition
from bluebottle.test.factory_models.projects import ProjectFactory


class PayoutBaseTestCase(BluebottleTestCase):
    """ Base test case for Payouts. """

    def setUp(self):
        super(PayoutBaseTestCase, self).setUp()

        self.init_projects()

        # Set up a project ready for payout
        self.organization = OrganizationFactory.create()
        self.organization.save()
        self.project = ProjectFactory.create(organization=self.organization, amount_asked=50)
        self.project_incomplete = ProjectFactory.create(organization=self.organization, amount_asked=100)

        # Update phase to campaign.
        self.project.status = ProjectPhase.objects.get(slug='campaign')
        self.project.save()

        self.project_incomplete.status = ProjectPhase.objects.get(slug='campaign')
        self.project_incomplete.save()

        self.order = OrderFactory.create()

        self.donation = DonationFactory.create(
            project=self.project,
            order=self.order,
            amount=60
        )
        self.donation.save()

        self.donation2 = DonationFactory.create(
            project=self.project_incomplete,
            order=self.order,
            amount=60
        )
        self.donation2.save()


@override_settings(
    MULTI_TENANT_DIR=os.path.join(settings.PROJECT_ROOT, 'bluebottle', 'test',
                                  'properties'))
class PayoutTestCase(PayoutBaseTestCase):
    """ Test case for Payouts. """

    def test_save(self):
        """ Test saving a payout. """

        # Generate new payout
        payout = ProjectPayoutFactory.create(completed=None)

        # Validate
        payout.clean()

        # Save it
        payout.save()

    def test_unicode(self):
        """ Test unicode() on payout. """

        payout = ProjectPayoutFactory.create()
        self.assertTrue(unicode(payout))

    def test_completed(self):
        """ Test the transition to settled. """

        payout = ProjectPayoutFactory.create(
            completed=None, status=StatusDefinition.IN_PROGRESS)
        payout.save()

        self.assertFalse(payout.completed)

        # Change status to settled
        payout.settled()
        payout.save()

        # Completed date should now be set
        self.assertTrue(payout.completed)

    def test_create_payout(self):
        """
        Test automatically generating a payout.
        """

        # No payouts should exist yet as project is not in act phase yet
        self.assertFalse(ProjectPayout.objects.exists())

        # Set status of donation to pending
        self.donation.order.locked()
        self.donation.order.save()
        self.donation.order.pending()
        self.donation.order.save()

        # Update phase to act.
        self.project.refresh_from_db()
        self.project.status = ProjectPhase.objects.get(slug='done-complete')
        self.project.save()

        # Payout should have been created
        self.assertEquals(ProjectPayout.objects.count(), 1)

        payout = ProjectPayout.objects.all()[0]

        # Check the project and the amount
        self.assertEquals(payout.project, self.project)
        self.assertEquals(payout.amount_raised, Money(60.00, 'EUR'))

    def test_dont_create_payout(self):
        """
        Test that a payout is not generated when the campaign never started
        """

        organization = OrganizationFactory.create()

        project = ProjectFactory.create(
            organization=organization, amount_asked=50)

        # No payouts should exist yet as project is not in act phase yet
        self.assertFalse(ProjectPayout.objects.exists())

        self.assertEqual(project.status,
                         ProjectPhase.objects.get(slug='plan-new'))

        # Payout should not have been created
        self.assertEquals(ProjectPayout.objects.count(), 0)

    def test_invoice_reference(self):
        """ Test generating invoice_reference. """

        # Set status of donation to paid
        self.donation.order.locked()
        self.donation.order.save()
        self.donation.order.success()
        self.donation.order.save()

        # Update phase to act.
        self.project.refresh_from_db()()
        self.project.status = ProjectPhase.objects.get(slug='done-complete')
        self.project.save()

        # Fetch payout
        payout = ProjectPayout.objects.all()[0]

        self.assertIn(str(self.project.id), payout.invoice_reference)
        self.assertIn(str(payout.id), payout.invoice_reference)

    def test_create_payment_rule_five(self):
        """ Projects should get payment rule five. """

        # Set status of donation to paid
        self.donation.order.locked()
        self.donation.order.save()
        self.donation.order.success()
        self.donation.order.save()

        # Update phase to act.
        self.project.refresh_from_db()()
        self.project.status = ProjectPhase.objects.get(slug='done-complete')
        self.project.save()

        payout = ProjectPayout.objects.all()[0]
        payout.payout_rule = 'five'
        payout.calculate_amounts()

        self.assertEquals(payout.payout_rule, ProjectPayout.PayoutRules.five)
        self.assertEquals(payout.organization_fee, Money('3', 'EUR'))
        self.assertEquals(payout.amount_payable, Money('57', 'EUR'))

    def test_amounts_new(self):
        """ Test amounts for new donations. """

        # Update phase to act.
        self.project.refresh_from_db()()
        self.project.status = ProjectPhase.objects.get(slug='done-complete')
        self.project.save()

        # Fetch payout
        payout = ProjectPayout.objects.all()[0]

        # No money is even pending
        self.assertEquals(payout.amount_raised, Money(0.00, 'EUR'))
        self.assertEquals(payout.amount_payable, Money(0.00, 'EUR'))

        self.assertEquals(payout.get_amount_pending(), Money(0.00, 'EUR'))
        self.assertEquals(payout.get_amount_safe(), Money(0.00, 'EUR'))
        self.assertEquals(payout.get_amount_failed(), Money(0.00, 'EUR'))

    def test_amounts_pending(self):
        """ Test amounts for pending donations. """

        # Set status of donation
        self.donation.order.locked()
        self.donation.order.save()
        self.donation.order.pending()
        self.donation.order.save()

        # Update phase to act.
        self.project.refresh_from_db()()
        self.project.status = ProjectPhase.objects.get(slug='done-complete')
        self.project.save()

        # Fetch payout
        payout = ProjectPayout.objects.all()[0]

        # Money is pending but not paid
        self.assertEquals(payout.amount_raised, Money(60.00, 'EUR'))
        self.assertEquals(payout.payout_rule, 'fully_funded')
        self.assertEquals(payout.amount_payable, Money(55.80, 'EUR'))

        self.assertEquals(payout.get_amount_pending(), Money(60.00, 'EUR'))
        self.assertEquals(payout.get_amount_safe(), Money(0.00, 'EUR'))
        self.assertEquals(payout.get_amount_failed(), Money(0.00, 'EUR'))

    def test_amounts_failed(self):
        """
        Test amounts for pending donation changed into failed after creating
        payout.
        """

        # Set status of donation to pending first
        self.donation.order.locked()
        self.donation.order.save()
        self.donation.order.pending()
        self.donation.order.save()

        # Update phase to act.
        self.project.refresh_from_db()()
        self.project.status = ProjectPhase.objects.get(slug='done-complete')
        self.project.save()

        # Set status of donation to failed
        self.donation.order.failed()
        self.donation.order.save()

        # Fetch payout
        payout = ProjectPayout.objects.all()[0]

        # Saved amounts should be same as pending
        self.assertEquals(payout.amount_raised, Money(0.00, 'EUR'))
        self.assertEquals(payout.amount_payable, Money(0.00, 'EUR'))

        # Real time amounts should be different
        self.assertEquals(payout.get_amount_pending(), Money(0.00, 'EUR'))
        self.assertEquals(payout.get_amount_safe(), Money(0.00, 'EUR'))
        self.assertEquals(payout.get_amount_failed(), Money(0.00, 'EUR'))

    def test_amounts_paid(self):
        """ Test amounts for paid donations. """

        # Setup organization
        organization = self.project.organization
        organization.account_name = 'Funny organization'
        organization.account_iban = 'NL90ABNA0111111111'
        organization.account_bic = 'ABNANL2A'
        organization.save()

        # Set status of donation to paid
        self.donation.order.locked()
        self.donation.order.save()
        self.donation.order.success()
        self.donation.order.save()

        # Update phase to act.
        self.project.refresh_from_db()()
        self.project.status = ProjectPhase.objects.get(slug='done-complete')
        self.project.save()

        # Fetch payout
        payout = ProjectPayout.objects.all()[0]

        # Money is safe now, nothing pending
        self.assertEquals(payout.amount_raised, Money(60.00, 'EUR'))

        self.assertEquals(payout.payout_rule, 'fully_funded')
        self.assertEquals(payout.amount_payable, Money(55.80, 'EUR'))

        self.assertEquals(payout.amount_pending, Money(0.00, 'EUR'))
        self.assertEquals(payout.amount_safe, Money(60.00, 'EUR'))
        self.assertEquals(payout.amount_failed, Money(0.00, 'EUR'))

    def test_amounts_paid_fully_funded(self):
        """ Test amounts for paid donations. """

        # Setup organization
        organization = self.project.organization
        organization.account_name = 'Funny organization'
        organization.account_iban = 'NL90ABNA0111111111'
        organization.account_bic = 'ABNANL2A'
        organization.save()

        # Set status of donation to paid
        self.donation.order.locked()
        self.donation.order.save()
        self.donation.order.success()
        self.donation.order.save()

        # Update phase to act.
        self.project.refresh_from_db()()
        self.project.status = ProjectPhase.objects.get(slug='done-complete')
        self.project.save()

        # Fetch payout
        payout = ProjectPayout.objects.all()[0]

        # Money is safe now, nothing pending
        self.assertEquals(payout.amount_raised, Money(60.00, 'EUR'))
        self.assertEquals(payout.payout_rule, 'fully_funded')
        self.assertEquals(payout.amount_payable, Money(55.80, 'EUR'))

        self.assertEquals(payout.amount_pending, Money(0.00, 'EUR'))
        self.assertEquals(payout.amount_safe, Money(60.00, 'EUR'))
        self.assertEquals(payout.amount_failed, Money(0.00, 'EUR'))

    def test_amounts_paid_not_fully_funded(self):
        """ Test amounts for paid donations. """

        # Setup organization
        organization = self.project.organization
        organization.account_name = 'Funny organization'
        organization.account_iban = 'NL90ABNA0111111111'
        organization.account_bic = 'ABNANL2A'
        organization.save()

        # Set status of donation to paid
        self.donation2.order.locked()
        self.donation2.order.save()
        self.donation2.order.success()
        self.donation2.order.save()

        # Update phase to act.
        self.project.refresh_from_db()()
        self.project_incomplete.status = ProjectPhase.objects.get(slug='done-incomplete')
        self.project_incomplete.save()

        # Fetch payout
        payout = ProjectPayout.objects.all()[0]

        # Money is safe now, nothing pending
        self.assertEquals(payout.amount_raised, Money(60.00, 'EUR'))
        self.assertEquals(payout.payout_rule, 'not_fully_funded')
        self.assertEquals(payout.amount_payable, Money(52.80, 'EUR'))

        self.assertEquals(payout.amount_pending, Money(0.00, 'EUR'))
        self.assertEquals(payout.amount_safe, Money(60.00, 'EUR'))
        self.assertEquals(payout.amount_failed, Money(0.00, 'EUR'))

    @override_settings(PROJECT_PAYOUT_FEES={'beneath_threshold': 1, 'fully_funded': .1, 'not_fully_funded': .5})
    def test_changed_fees_amounts_paid_fully_funded(self):
        """ Test amounts for paid donations. """

        # Setup organization
        organization = self.project.organization
        organization.account_name = 'Funny organization'
        organization.account_iban = 'NL90ABNA0111111111'
        organization.account_bic = 'ABNANL2A'
        organization.save()

        # Set status of donation to paid
        self.donation.order.locked()
        self.donation.order.save()
        self.donation.order.success()
        self.donation.order.save()

        # Update phase to act.
        self.project.refresh_from_db()()
        self.project.status = ProjectPhase.objects.get(slug='done-complete')
        self.project.save()

        # Fetch payout
        payout = ProjectPayout.objects.all()[0]

        # Money is safe now, nothing pending
        self.assertEquals(payout.amount_raised, Money(60.00, 'EUR'))
        self.assertEquals(payout.payout_rule, 'fully_funded')
        self.assertEquals(payout.amount_payable, Money(55.80, 'EUR'))

        self.assertEquals(payout.amount_pending, Money(0.00, 'EUR'))
        self.assertEquals(payout.amount_safe, Money(60.00, 'EUR'))
        self.assertEquals(payout.amount_failed, Money(0.00, 'EUR'))

    @override_settings(PROJECT_PAYOUT_FEES={'beneath_threshold': 1, 'fully_funded': .1, 'not_fully_funded': .5})
    def test_changed_fees_amounts_paid_not_fully_funded(self):
        """ Test amounts for paid donations. """

        # Setup organization
        organization = self.project.organization
        organization.account_name = 'Funny organization'
        organization.account_iban = 'NL90ABNA0111111111'
        organization.account_bic = 'ABNANL2A'
        organization.save()

        # Set status of donation to paid
        self.donation2.order.locked()
        self.donation2.order.save()
        self.donation2.order.success()
        self.donation2.order.save()

        # Update phase to act.
        self.project.refresh_from_db()()
        self.project_incomplete.status = ProjectPhase.objects.get(
            slug='done-incomplete')
        self.project_incomplete.save()

        # Fetch payout
        payout = ProjectPayout.objects.all()[0]

        # Money is safe now, nothing pending
        self.assertEquals(payout.amount_raised, Money(60.00, 'EUR'))
        self.assertEquals(payout.payout_rule, 'not_fully_funded')
        self.assertEquals(payout.amount_payable, Money(52.80, 'EUR'))

        self.assertEquals(payout.amount_pending, Money(0.00, 'EUR'))
        self.assertEquals(payout.amount_safe, Money(60.00, 'EUR'))
        self.assertEquals(payout.amount_failed, Money(0.00, 'EUR'))

    def test_changed_fees_amounts_beneath_threshold(self):
        """ Test amounts when donations are beneath minimal payout amount. """

        # Setup organization
        organization = self.project.organization
        organization.account_name = 'Funny organization'
        organization.account_iban = 'NL90ABNA0111111111'
        organization.account_bic = 'ABNANL2A'
        organization.save()

        beneath_threshold_project = ProjectFactory.create(
            organization=organization, amount_asked=50)

        # Update phase to campaign.
        beneath_threshold_project.status = ProjectPhase.objects.get(
            slug='campaign')
        a_week_ago = timezone.now() - timezone.timedelta(days=7)
        beneath_threshold_project.campaign_started = a_week_ago
        beneath_threshold_project.save()

        order = OrderFactory.create()
        donation = DonationFactory.create(
            project=beneath_threshold_project,
            order=order,
            amount=5
        )
        donation.save()
        donation.order.locked()
        donation.order.save()
        donation.order.success()
        donation.order.save()

        # Update phase to act.
        self.project.refresh_from_db()()
        beneath_threshold_project.status = ProjectPhase.objects.get(
            slug='done-incomplete')
        beneath_threshold_project.save()

        # Fetch payout
        payout = ProjectPayout.objects.all()[0]

        # Money is safe now, nothing pending
        self.assertEquals(payout.amount_raised, Money(5.00, 'EUR'))
        self.assertEquals(payout.payout_rule, 'beneath_threshold')
        self.assertEquals(payout.amount_payable, Money(0.00, 'EUR'))

        self.assertEquals(payout.amount_pending, Money(0.00, 'EUR'))
        self.assertEquals(payout.amount_safe, Money(5.00, 'EUR'))
        self.assertEquals(payout.amount_failed, Money(0.00, 'EUR'))

    def test_beneath_threshold_status_completed(self):
        """
        Test that a payout with payout rule 'beneath_threshold' and no
        pending donations gets the status 'settled'.
        """
        self.assertFalse(ProjectPayout.objects.exists())

        project = ProjectFactory.create(amount_asked=100)
        project.campaign_started = timezone.now() - timezone.timedelta(days=10)
        project.status = ProjectPhase.objects.get(slug='done-incomplete')
        project.save()

        # Fetch payout
        self.assertEquals(ProjectPayout.objects.count(), 1)
        payout = ProjectPayout.objects.all()[0]
        self.assertEquals(payout.payout_rule, 'beneath_threshold')
        self.assertEquals(payout.amount_payable, Money(0.00, 'EUR'))
        self.assertEqual(Donation.objects.filter(project=project)
                         .count(), 0)
        self.assertEqual(payout.completed, timezone.now().date())
        self.assertEqual(payout.status, 'settled')
        self.assertTrue(payout.completed)

    def test_beneath_threshold_status_not_completed_pending_payments(self):
        """
        Test that a payout with rule 'beneath_threshold' but with pending
        donations does not get the status 'settled'.
        """
        self.assertFalse(ProjectPayout.objects.exists())

        project = ProjectFactory.create(amount_asked=100)
        project.campaign_started = timezone.now() - timezone.timedelta(days=10)
        project.save()

        order = OrderFactory.create()

        donation = DonationFactory.create(
            project=project,
            order=order,
            amount=1
        )
        donation.save()

        # Set status of donation to pending
        donation.order.locked()
        donation.order.save()
        donation.order.pending()
        donation.order.save()

        self.assertEqual(donation.status, 'pending')

        project.status = ProjectPhase.objects.get(slug='done-incomplete')
        project.save()

        # Fetch payout
        self.assertEquals(ProjectPayout.objects.count(), 1)
        payout = ProjectPayout.objects.all()[0]

        self.assertEquals(payout.payout_rule, 'beneath_threshold')
        self.assertEquals(payout.amount_payable, Money(0.00, 'EUR'))
        self.assertEqual(Donation.objects.filter(project=project)
                         .count(), 1)
        self.assertEqual(payout.status, 'new')
        self.assertTrue(not payout.completed)

    def test_invalid_iban(self):
        """
        Test that the iban field is not populated if the account number
        is not a valid IBAN
        """
        self.project.account_number = "nefwkjfnwkflewblablabla"
        self.project.save()

        # Set status of donation to paid
        self.donation.order.locked()
        self.donation.order.save()
        self.donation.order.success()
        self.donation.order.save()

        # Update phase to act.
        self.project.refresh_from_db()()
        self.project.status = ProjectPhase.objects.get(slug='done-complete')
        self.project.save()

        # Fetch payout
        payout = ProjectPayout.objects.all()[0]

        self.assertEqual(payout.receiver_account_iban, '')

    def test_valid_iban_nl(self):
        """
        Test that the iban field is populated if the account number is
        valid Dutch account
        """
        self.project.account_number = "NL91ABNA0417164300"
        self.project.save()

        # Set status of donation to paid
        self.donation.order.locked()
        self.donation.order.save()
        self.donation.order.success()
        self.donation.order.save()

        # Update phase to act.
        self.project.refresh_from_db()()
        self.project.status = ProjectPhase.objects.get(slug='done-complete')
        self.project.save()

        # Fetch payout
        payout = ProjectPayout.objects.all()[0]

        self.assertEqual(payout.receiver_account_iban, 'NL91ABNA0417164300')

    def test_valid_iban_de(self):
        """
        Test that the iban field is populated if the account number
        is a valid German account"""
        self.project.account_number = "DE89370400440532013000"
        self.project.save()

        # Set status of donation to paid
        self.donation.order.locked()
        self.donation.order.save()
        self.donation.order.success()
        self.donation.order.save()

        # Update phase to act.
        self.project.refresh_from_db()()
        self.project.status = ProjectPhase.objects.get(slug='done-complete')
        self.project.save()

        # Fetch payout
        payout = ProjectPayout.objects.all()[0]

        self.assertEqual(payout.receiver_account_iban,
                         'DE89370400440532013000')

    def test_protected_payout(self):
        """
        Test that a protected payout cannot be recalculated and does not return
        the `project` amounts.
        """
        self.donation.order.locked()
        self.donation.order.save()
        self.donation.order.pending()
        self.donation.order.save()

        self.project.refresh_from_db()()
        self.assertEqual(self.project.amount_donated, Money(60, 'EUR'))

        payout1 = ProjectPayoutFactory.create(
            project=self.project,
            status=StatusDefinition.NEW,
            protected=False
        )
        payout1 = payout1.__class__.objects.get(pk=payout1.pk)
        payout1.calculate_amounts()
        self.assertEqual(payout1.amount_raised, Money(60, 'EUR'))

        payout2 = ProjectPayoutFactory.create(
            completed=None,
            status=StatusDefinition.NEW,
            protected=True,
            amount_raised=Decimal(10),
            amount_payable=Decimal(10),
            organization_fee=0
        )
        self.assertEqual(payout2.get_amount_raised(), Money(10, 'EUR'))
        self.assertEqual(payout2.get_amount_safe(), Money(10, 'EUR'))
        self.assertEqual(payout2.get_amount_pending(), Money(0, 'EUR'))
        self.assertEqual(payout2.get_amount_failed(), Money(0, 'EUR'))

        with self.assertRaises(AssertionError):
            payout2.calculate_amounts()


@override_settings(PROJECT_PAYOUT_FEES={'beneath_threshold': 1, 'fully_funded': .1, 'not_fully_funded': .2})
class PayoutPledgeTestCase(PayoutBaseTestCase):
    """ Test case for Pledge Payouts. """

    def setUp(self):
        super(PayoutPledgeTestCase, self).setUp()

        self.project = ProjectFactory.create(organization=self.organization, amount_asked=100)

        # Update phase to campaign.
        self.project.status = ProjectPhase.objects.get(slug='campaign')
        self.project.save()

        self.order = OrderFactory.create()

        self.donation = DonationFactory.create(
            project=self.project,
            order=self.order,
            amount=60
        )

        self.donation.save()

        # Set status of donation to paid
        self.donation.order.locked()
        self.donation.order.save()
        self.donation.order.success()
        self.donation.order.save()

    def test_pledge_paid_fully_funded(self):
        """ Test amounts for paid donations. """

        pledge_order = OrderFactory.create()
        pledge = DonationFactory.create(
            project=self.project,
            order=pledge_order,
            amount=60
        )
        pledge.save()

        # Set status of donation to pledged
        pledge.order.pledged()
        pledge.order.save()

        # Update phase to done-completed
        self.project.refresh_from_db()()
        self.project.status = ProjectPhase.objects.get(slug='done-complete')
        self.project.save()

        # Fetch payout
        payout = ProjectPayout.objects.all()[0]

        # Money is safe now, nothing pending
        self.assertEquals(payout.amount_raised, Money(120.00, 'EUR'))
        self.assertEquals(payout.payout_rule, 'fully_funded')
        self.assertEquals(payout.amount_payable, Money(54.00, 'EUR'))
        self.assertEquals(payout.amount_pledged, Money(60.00, 'EUR'))
        self.assertEquals(payout.organization_fee, Money(6.00, 'EUR'))

    def test_pledge_paid_not_fully_funded(self):
        """ Test amounts for paid donations. """

        pledge_order = OrderFactory.create()
        pledge = DonationFactory.create(
            project=self.project,
            order=pledge_order,
            amount=30
        )
        pledge.save()

        # Set status of donation to pledged
        pledge.order.pledged()
        pledge.order.save()

        # Update phase to done-completed
        self.project.refresh_from_db()()
        self.project.status = ProjectPhase.objects.get(slug='done-complete')
        self.project.save()

        # Fetch payout
        payout = ProjectPayout.objects.all()[0]

        # Money is safe now, nothing pending
        self.assertEquals(payout.amount_raised, Money(90.00, 'EUR'))
        self.assertEquals(payout.payout_rule, 'not_fully_funded')
        self.assertEquals(payout.amount_payable, Money(48.00, 'EUR'))
        self.assertEquals(payout.amount_pledged, Money(30.00, 'EUR'))
        self.assertEquals(payout.organization_fee, Money(12.00, 'EUR'))
