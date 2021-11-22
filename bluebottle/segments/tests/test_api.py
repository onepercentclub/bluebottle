# coding=utf-8
from builtins import str
from builtins import range
from django.urls import reverse

from rest_framework import status

from bluebottle.members.models import MemberPlatformSettings
from bluebottle.segments.models import Segment, SegmentType
from bluebottle.segments.tests.factories import SegmentFactory, SegmentTypeFactory
from bluebottle.segments.serializers import SegmentSerializer

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient, APITestCase


class SegmentTypeListAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(SegmentTypeListAPITestCase, self).setUp()

        self.client = JSONAPITestClient()

        self.url = reverse('segment-type-list')
        self.user = BlueBottleUserFactory()

        for i in range(5):
            segment_type = SegmentTypeFactory.create()
            SegmentFactory.create_batch(
                3,
                type=segment_type
            )

    def test_list(self):
        response = self.client.get(self.url, user=self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            len(response.json()['data']), 5
        )
        result = response.json()['data'][0]

        segment_type = SegmentType.objects.get(pk=result['id'])

        self.assertEqual(segment_type.name, result['attributes']['name'])
        self.assertEqual(
            set(relation['id'] for relation in result['relationships']['segments']['data']),
            set(str(segment.pk) for segment in segment_type.segments.all())
        )

    def test_list_anonymous(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            len(response.json()['data']), 5
        )

    def test_list_closed(self):
        MemberPlatformSettings.objects.update(closed=True)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_inactive(self):
        SegmentTypeFactory.create(is_active=False)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            len(response.json()['data']), 5
        )


class SegmentListAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(SegmentListAPITestCase, self).setUp()

        self.client = JSONAPITestClient()

        self.url = reverse('segment-list')
        self.user = BlueBottleUserFactory()
        self.segment_type = SegmentTypeFactory.create()
        self.segments = SegmentFactory.create_batch(
            20,
            type=self.segment_type
        )

    def test_list(self):
        response = self.client.get(self.url, user=self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            len(response.json()['data']), 20
        )
        result = response.json()['data'][0]

        segment = Segment.objects.get(pk=result['id'])

        self.assertEqual(segment.name, result['attributes']['name'])
        self.assertEqual(
            str(segment.type_id),
            result['relationships']['type']['data']['id']
        )

    def test_list_anonymous(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            len(response.json()['data']), 20
        )

    def test_list_closed(self):
        MemberPlatformSettings.objects.update(closed=True)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_inactive(self):
        inactive_type = SegmentTypeFactory(is_active=False)
        SegmentFactory.create(type=inactive_type)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            len(response.json()['data']), 20
        )


class SegmentDetailAPITestCase(APITestCase):

    def setUp(self):
        super().setUp()

        self.serializer = SegmentSerializer
        self.factory = SegmentFactory

        self.segment_type = SegmentTypeFactory.create()
        self.model = SegmentFactory.create(type=self.segment_type)

        self.fields = []

        self.url = reverse('segment-detail', args=(self.model.pk, ))

    def test_retrieve(self):
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)
        self.assertIncluded('type', self.segment_type)
        self.assertAttribute('name', self.model.name)
        self.assertAttribute('slug', self.model.slug)

    def test_retrieve_closed(self):
        with self.closed_site():
            self.perform_get()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_closed_user(self):
        with self.closed_site():
            self.perform_get(user=BlueBottleUserFactory.create())

        self.assertStatus(status.HTTP_200_OK)

    def test_update(self):
        self.perform_update({'name': 'test'})

        self.assertStatus(status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete(self):
        self.perform_delete()

        self.assertStatus(status.HTTP_405_METHOD_NOT_ALLOWED)
