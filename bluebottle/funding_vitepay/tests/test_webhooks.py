import bunch
from django.urls import reverse
from rest_framework.status import HTTP_200_OK

from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.funding.transitions import PaymentTransitions
from bluebottle.funding_vitepay.models import VitepayPaymentProvider
from bluebottle.funding_vitepay.tests.factories import VitepayPaymentFactory, VitepayPaymentProviderFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class MockEvent(object):
    def __init__(self, type, data):
        self.type = type
        self.data = bunch.bunchify(data)


class VitepayPaymentTestCase(BluebottleTestCase):

    def setUp(self):
        super(VitepayPaymentTestCase, self).setUp()
        VitepayPaymentProvider.objects.all().delete()
        VitepayPaymentProviderFactory.create()

        self.initiative = InitiativeFactory.create()
        self.initiative.states.approve(save=True)

        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonationFactory.create(activity=self.funding)
        self.payment = VitepayPaymentFactory.create(
            donation=self.donation,
            unique_id='some-id',
        )
        self.webhook = reverse('vitepay-payment-webhook')

    def test_success(self):
        data = {
            'success': 1,
            'authenticity': 'FD549FB47E4D85B5593F5D48C3D524AAD933CBEB',
            'order_id': 'some-id'
        }
        response = self.client.post(self.webhook, data, format='multipart')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.content, '{"status": "1"}')
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, PaymentTransitions.values.succeeded)

    def test_failed(self):
        data = {
            'failure': 1,
            'authenticity': 'FD549FB47E4D85B5593F5D48C3D524AAD933CBEB',
            'order_id': 'some-id'
        }
        response = self.client.post(self.webhook, data, format='multipart')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.content, '{"status": "1"}')
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, PaymentTransitions.values.failed)

    def test_not_found(self):
        data = {
            'failure': 1,
            'authenticity': 'FD549FB47E4D85B5593F5D48C3D524AAD933CBEB',
            'order_id': 'another-id'
        }
        response = self.client.post(self.webhook, data, format='multipart')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.content, '{"status": "0", "message": "Order not found."}')
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, PaymentTransitions.values.new)
