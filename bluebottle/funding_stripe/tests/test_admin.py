import stripe
from django.urls import reverse
from djmoney.money import Money
from unittest.mock import patch
from rest_framework import status

from bluebottle.funding.tests.factories import (
    DonationFactory, FundingFactory
)
from bluebottle.funding_stripe.tests.factories import StripeSourcePaymentFactory, ExternalAccountFactory
from bluebottle.funding_stripe.tests.utils import generate_stripe_payout_account
from bluebottle.test.utils import BluebottleAdminTestCase


class StripeSourcePaymentAdminTestCase(BluebottleAdminTestCase):
    def setUp(self):
        super().setUp()
        account = generate_stripe_payout_account()
        bank_account = ExternalAccountFactory.create(connect_account=account)
        funding = FundingFactory.create(bank_account=bank_account)
        self.client.force_login(self.superuser)
        self.donation = DonationFactory(
            amount=Money(100, 'EUR'),
            activity=funding
        )
        with patch('stripe.Source.modify'):
            self.payment = StripeSourcePaymentFactory.create(
                source_token='source-token',
                charge_token='charge-token',
                donation=self.donation
            )
        self.admin_url = reverse('admin:funding_stripe_stripesourcepayment_change', args=(self.payment.id,))
        self.check_status_url = reverse('admin:funding_payment_check', args=(self.payment.id,))
        self.source = stripe.Source('source-token')
        self.source.update({
            'amount': 10000,
            'currency': 'EUR',
            'status': 'charged'
        })
        self.charge = stripe.Charge('charge-token')
        self.charge.update({
            'status': 'succeeded',
            'refunded': None,
            'dispute': None
        })

    def test_check_adjust_donation_amount(self):
        self.source.update({
            'amount': 35000
        })
        with patch('stripe.Source.retrieve', return_value=self.source),  \
                patch('stripe.Charge.retrieve', return_value=self.charge):
            response = self.client.get(self.check_status_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.amount, Money(350, 'EUR'))

    def test_check_chargeable(self):
        self.source.update({
            'status': 'chargeable'
        })
        self.payment.charge_token = None
        self.payment.save()
        with patch('stripe.Source.retrieve', return_value=self.source),  \
                patch('stripe.Charge.create', return_value=self.charge), \
                patch('stripe.Charge.retrieve', return_value=self.charge):
            response = self.client.get(self.check_status_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'succeeded')
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'succeeded')

    def test_check_payment_source_failed(self):
        self.source.update({
            'status': 'failed'
        })
        self.payment.charge_token = None
        self.payment.save()
        with patch('stripe.Source.retrieve', return_value=self.source), \
                patch('stripe.Charge.retrieve', return_value=self.charge):
            response = self.client.get(self.check_status_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'failed')

    def test_check_payment_source_canceled(self):
        self.source.update({
            'status': 'canceled'
        })
        self.payment.charge_token = None
        self.payment.save()
        with patch('stripe.Source.retrieve', return_value=self.source), \
                patch('stripe.Charge.retrieve', return_value=self.charge):
            response = self.client.get(self.check_status_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.payment.refresh_from_db()
        self.donation.refresh_from_db()
        self.assertEqual(self.payment.status, 'canceled')
        self.assertEqual(self.donation.status, 'failed')

    def test_check_payment_charge_failed(self):
        self.charge.update({
            'status': 'failed'
        })
        with patch('stripe.Source.retrieve', return_value=self.source), \
                patch('stripe.Charge.retrieve', return_value=self.charge):
            response = self.client.get(self.check_status_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'failed')

    def test_check_payment_charge_disputed(self):
        self.charge.update({
            'dispute': 'closed'
        })
        with patch('stripe.Source.retrieve', return_value=self.source), \
                patch('stripe.Charge.retrieve', return_value=self.charge):
            response = self.client.get(self.check_status_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.payment.refresh_from_db()
        self.donation.refresh_from_db()
        self.assertEqual(self.payment.status, 'disputed')
        self.assertEqual(self.donation.status, 'refunded')

    def test_check_payment_charge_refunded(self):
        self.charge.update({
            'refunded': True
        })
        with patch('stripe.Source.retrieve', return_value=self.source), \
                patch('stripe.Charge.retrieve', return_value=self.charge):
            response = self.client.get(self.check_status_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.payment.refresh_from_db()
        self.donation.refresh_from_db()
        self.assertEqual(self.payment.status, 'refunded')
        self.assertEqual(self.donation.status, 'refunded')
