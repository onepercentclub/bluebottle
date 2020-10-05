import json

from django.urls import reverse
from mock import patch
from rest_framework import status

from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.funding_vitepay.models import VitepayPaymentProvider
from bluebottle.funding_vitepay.tests.factories import VitepayPaymentProviderFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class VitepayPaymentTestCase(BluebottleTestCase):

    def setUp(self):
        super(VitepayPaymentTestCase, self).setUp()
        VitepayPaymentProvider.objects.all().delete()
        VitepayPaymentProviderFactory.create()

        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonationFactory.create(activity=self.funding, user=self.user)

        self.payment_url = reverse('vitepay-payment-list')

        self.data = {
            'data': {
                'type': 'payments/vitepay-payments',
                'attributes': {
                },
                'relationships': {
                    'donation': {
                        'data': {
                            'type': 'contributions/donations',
                            'id': self.donation.pk,
                        }
                    }
                }
            }
        }

    @patch('bluebottle.funding_vitepay.utils.requests.post',
           return_value=type('obj', (object,),
                             {'status_code': 200, 'content': 'https://vitepay.com/some-path-to-pay'}))
    def test_create_payment(self, vitepay_post):
        response = self.client.post(self.payment_url, data=json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['status'], 'new')
        self.assertEqual(data['data']['attributes']['payment-url'], 'https://vitepay.com/some-path-to-pay')
        self.assertEqual(data['included'][0]['attributes']['status'], 'new')
