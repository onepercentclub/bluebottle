import stripe
from django.urls import reverse
from djmoney.money import Money
from mock import patch
from rest_framework import status

from bluebottle.funding.tests.factories import (
    DonationFactory
)
from bluebottle.funding_stripe.tests.factories import StripeSourcePaymentFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class StripeSourcePaymentAdminTestCase(BluebottleAdminTestCase):
    def setUp(self):
        super(StripeSourcePaymentAdminTestCase, self).setUp()
        self.client.force_login(self.superuser)
        self.donation = DonationFactory(
            amount=Money(100, 'EUR')
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

    def test_check_payment_success(self):
        with patch('stripe.Source.retrieve', return_value=self.source), \
                patch('stripe.Charge.retrieve', return_value=self.charge):
            response = self.client.get(self.check_status_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'succeeded')
