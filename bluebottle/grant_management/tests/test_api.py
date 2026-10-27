from django.urls import reverse
from rest_framework import status

from bluebottle.grant_management.serializers import GrantApplicationSerializer
from bluebottle.grant_management.tests.factories import GrantApplicationFactory, GrantDonorFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import APITestCase


class GrantApplicationApiTestCase(APITestCase):
    factory = GrantApplicationFactory

    def setUp(self):
        super().setUp()
        self.serializer = GrantApplicationSerializer
        self.model = self.factory(status='draft', initiative=None)
        self.url = reverse('grant-application-detail', args=(self.model.id,))
        self.admin = BlueBottleUserFactory.create(is_superuser=True)

    def test_submit(self):
        self.perform_get(user=self.admin)
        self.assertStatus(status.HTTP_200_OK)
        self.assertResourceStatus(self.model, 'draft')
        self.assertTransition('submit')
        self.model.states.submit(save=True)

        self.perform_get(user=self.admin)
        self.assertStatus(status.HTTP_200_OK)
        self.assertResourceStatus(self.model, 'submitted')
        self.assertNotTransition('submit')
        # Can't approve through API
        self.assertNotTransition('approve')

        # Adding a grant will approve/grant the application
        GrantDonorFactory.create(
            activity=self.model,
        )
        self.assertResourceStatus(self.model, 'granted')
