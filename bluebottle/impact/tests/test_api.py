# coding=utf-8
from django.urls import reverse
from rest_framework import status

from bluebottle.impact.tests.factories import (
    ImpactTypeFactory,  # ImpactGoalFactory
)
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class ImpactTypeAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(ImpactTypeAPITestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.types = ImpactTypeFactory.create_batch(10)
        self.url = reverse('impact-type-list')
        self.user = BlueBottleUserFactory()

    def test_get(self):
        response = self.client.get(self.url, user=self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_anonymous(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_only_active(self):
        self.types[0].active = False
        self.types[0].save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_closed(self):
        MemberPlatformSettings.objects.update(closed=True)

        response = self.client.get(self.url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_closed_anonymous(self):
        MemberPlatformSettings.objects.update(closed=True)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post(self):
        response = self.client.post(self.url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
