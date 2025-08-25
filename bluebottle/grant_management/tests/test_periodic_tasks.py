from datetime import timedelta
from django.utils import timezone
from djmoney.money import Money
from unittest.mock import patch

from bluebottle.grant_management.models import GrantPayment
from bluebottle.grant_management.tasks import grant_provider_tasks
from bluebottle.grant_management.tests.factories import (
    GrantDonorFactory,
    GrantFundFactory,
    GrantPayoutFactory,
    GrantProviderFactory,
)
from bluebottle.test.utils import BluebottleTestCase


class GrantProviderScheduledTasksTestCase(BluebottleTestCase):

    def setUp(self):
        self.provider = GrantProviderFactory(
            payment_frequency=1,
        )
        self.fund = GrantFundFactory.create(
            grant_provider=self.provider,
        )

    def create_approved_payouts(self):
        """Create approved payouts for testing"""
        payouts = []
        grants = GrantDonorFactory.create_batch(
            3,
            amount=Money(1000, "EUR"),
            fund=self.fund,
        )

        for grant in grants:
            payout = GrantPayoutFactory.create(
                activity=grant.activity,
                provider=self.provider.name,
                currency="EUR",
                status="approved",
                payment=None,
            )
            grant.payout = payout
            grant.save()
            payouts.append(payout)
        return payouts

    def get_week_number(self, weeks_from_now=0):
        """Get week number for a specific number of weeks from now"""
        target_date = timezone.now() + timedelta(weeks=weeks_from_now)
        return target_date.isocalendar()[1]

    def run_periodic_task_for_week(self, week_number):
        """Run the periodic task for a specific week"""
        with patch("bluebottle.grant_management.periodic_tasks.now") as mock_now:
            # Mock the current date to be in the specified week

            mock_date = timezone.now().replace(
                year=timezone.now().year,
                month=1,
                day=1,
            ) + timedelta(weeks=(week_number - 1))
            mock_now.return_value = mock_date
            grant_provider_tasks()

    def test_weekly_schedule_frequency_1(self):
        """Test that payments are generated every week when frequency=1"""
        self.provider.payment_frequency = "1"
        self.provider.save()

        for week in range(1, 9):
            self.create_approved_payouts()
            initial_payment_count = GrantPayment.objects.count()

            # Run periodic task for this week
            self.run_periodic_task_for_week(week)

            # Check that a payment was created
            self.assertEqual(
                GrantPayment.objects.count(),
                initial_payment_count + 1,
                f"Payment should be created in week {week} for frequency=1",
            )

            # Verify the payment is linked to the provider
            latest_payment = GrantPayment.objects.latest("created")
            self.assertEqual(latest_payment.grant_provider, self.provider)
            self.assertEqual(latest_payment.status, "pending")
            self.assertEqual(latest_payment.payouts.count(), 3)

    def test_biweekly_schedule_frequency_2(self):
        """Test that payments are generated every 2 weeks when frequency=2"""
        self.provider.payment_frequency = "2"
        self.provider.save()

        for week in range(1, 9):
            self.create_approved_payouts()
            initial_payment_count = GrantPayment.objects.count()

            GrantPayment.objects.all().update(
                created=timezone.now() - timedelta(days=8)
            )

            # Run periodic task for this week
            self.run_periodic_task_for_week(week)

            # Check if payment should be created (every 2 weeks)
            if week % 2 == 0:
                self.assertEqual(
                    GrantPayment.objects.count(),
                    initial_payment_count + 1,
                    f"Payment should be created in week {week} for frequency=2",
                )

                # Verify the payment is linked to the provider
                latest_payment = GrantPayment.objects.latest("created")
                self.assertEqual(latest_payment.grant_provider, self.provider)
                self.assertEqual(latest_payment.status, "pending")
                self.assertEqual(latest_payment.payouts.count(), 6)
            else:
                self.assertEqual(
                    GrantPayment.objects.count(),
                    initial_payment_count,
                    f"No payment should be created in week {week} for frequency=2",
                )

    def test_monthly_schedule_frequency_4(self):
        """Test that payments are generated every 4 weeks when frequency=4"""
        self.provider.payment_frequency = "4"
        self.provider.save()

        for week in range(1, 9):
            self.create_approved_payouts()
            initial_payment_count = GrantPayment.objects.count()

            # Run periodic task for this week
            self.run_periodic_task_for_week(week)

            # Check if payment should be created (every 4 weeks)
            if week % 4 == 0:
                self.assertEqual(
                    GrantPayment.objects.count(),
                    initial_payment_count + 1,
                    f"Payment should be created in week {week} for frequency=4",
                )

                # Verify the payment is linked to the provider
                latest_payment = GrantPayment.objects.latest("created")
                self.assertEqual(latest_payment.grant_provider, self.provider)
                self.assertEqual(latest_payment.status, "pending")
                self.assertEqual(latest_payment.payouts.count(), 12)
            else:
                self.assertEqual(
                    GrantPayment.objects.count(),
                    initial_payment_count,
                    f"No payment should be created in week {week} for frequency=4",
                )

    def test_multiple_providers_different_frequencies(self):
        """Test multiple providers with different payment frequencies"""
        # Create providers with different frequencies
        provider_weekly = GrantProviderFactory(payment_frequency="1")
        provider_biweekly = GrantProviderFactory(payment_frequency="2")
        provider_monthly = GrantProviderFactory(payment_frequency="4")

        # Create funds and grants for each provider
        fund_weekly = GrantFundFactory.create(grant_provider=provider_weekly)
        fund_biweekly = GrantFundFactory.create(grant_provider=provider_biweekly)
        fund_monthly = GrantFundFactory.create(grant_provider=provider_monthly)

        for week in range(1, 9):

            grants_weekly = GrantDonorFactory.create_batch(2, fund=fund_weekly)
            grants_biweekly = GrantDonorFactory.create_batch(2, fund=fund_biweekly)
            grants_monthly = GrantDonorFactory.create_batch(2, fund=fund_monthly)

            for grants in [grants_weekly, grants_biweekly, grants_monthly]:
                for grant in grants:
                    payout = GrantPayoutFactory.create(
                        activity=grant.activity,
                        provider=grant.fund.grant_provider.name,
                        currency="EUR",
                        status="approved",
                        payment=None,
                    )
                    grant.payout = payout
                    grant.save()

            initial_payment_count = GrantPayment.objects.count()

            # Run periodic task for this week
            self.run_periodic_task_for_week(week)

            # Count expected payments for this week
            expected_payments = 0
            if week % 1 == 0:  # Weekly
                expected_payments += 1
            if week % 2 == 0:  # Biweekly
                expected_payments += 1
            if week % 4 == 0:  # Monthly
                expected_payments += 1

            self.assertEqual(
                GrantPayment.objects.count(),
                initial_payment_count + expected_payments,
                f"Expected {expected_payments} payments in week {week}",
            )

    def test_no_payments_when_no_approved_payouts(self):
        """Test that no payments are created when there are no approved payouts"""
        self.provider.payment_frequency = "1"
        self.provider.save()

        # Don't create any approved payouts

        # Test weeks 1-4
        for week in range(1, 5):
            initial_payment_count = GrantPayment.objects.count()

            # Run periodic task for this week
            self.run_periodic_task_for_week(week)

            # No payments should be created
            self.assertEqual(
                GrantPayment.objects.count(),
                initial_payment_count,
                f"No payment should be created in week {week} when no approved payouts exist",
            )

    def test_payment_linking_to_payouts(self):
        """Test that created payments are properly linked to payouts"""
        self.provider.payment_frequency = "1"
        self.provider.save()

        # Create approved payouts
        payouts = self.create_approved_payouts()

        # Run periodic task
        self.run_periodic_task_for_week(1)

        # Check that a payment was created
        self.assertEqual(GrantPayment.objects.count(), 1)
        payment = GrantPayment.objects.first()

        # Check that all payouts are linked to this payment
        for payout in payouts:
            payout.refresh_from_db()
            self.assertEqual(payout.payment, payment)
