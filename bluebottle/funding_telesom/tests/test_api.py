from builtins import object
import json

from django.urls import reverse
from mock import patch
from rest_framework import status

from bluebottle.funding.tests.factories import FundingFactory, DonorFactory
from bluebottle.funding_telesom.models import TelesomPaymentProvider, TelesomPayment
from bluebottle.funding_telesom.tests.factories import TelesomPaymentProviderFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class MockReponse(object):
    status_code = 200,

    def json(self):
        return {'params': {'state': 'APPROVED'}}


class TelesomPaymentTestCase(BluebottleTestCase):

    def setUp(self):
        super(TelesomPaymentTestCase, self).setUp()
        TelesomPaymentProvider.objects.all().delete()
        TelesomPaymentProviderFactory.create()

        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()

        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonorFactory.create(activity=self.funding, user=self.user)

        self.payment_url = reverse('telesom-payment-list')

        self.data = {
            'data': {
                'type': 'payments/telesom-payments',
                'attributes': {
                },
                'relationships': {
                    'donation': {
                        'data': {
                            'type': 'contributors/donations',
                            'id': self.donation.pk,
                        }
                    }
                }
            }
        }

    @patch('bluebottle.funding_telesom.tasks.requests.post', return_value=MockReponse())
    def test_create_payment(self, telesom_post):
        response = self.client.post(self.payment_url, data=json.dumps(self.data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)
        payment = TelesomPayment.objects.get(id=data['data']['id'])
        self.assertEqual(payment.status, 'succeeded')
