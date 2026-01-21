from io import BytesIO
from pprint import pprint

import mock
from django.test import RequestFactory
from requests import Response

from bluebottle.activity_pub.models import GoodDeed, CrowdFunding
from bluebottle.activity_pub.resources import Resource
from bluebottle.activity_pub.serializers.federated_activities import FederatedDateActivitySerializer
from bluebottle.activity_pub.serializers.json_ld import (
    DoGoodEventSerializer, GoodDeedSerializer, CrowdFundingSerializer
)
from bluebottle.activity_pub.serializers.triples import OrganizationSerializer
from bluebottle.activity_pub.tests.factories import (
    DoGoodEventFactory
)
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import DateActivityFactory

from django.core.files.base import File


class DoGoodEventSerializerTestCase(BluebottleTestCase):
    activity_pub_serializer = DoGoodEventSerializer
    federated_serializer = FederatedDateActivitySerializer
    factory = DateActivityFactory
    activity_pub_factory = DoGoodEventFactory

    def setUp(self):
        self.settings = SitePlatformSettings.objects.create(
            share_activities=['supplier', 'consumer']
        )
        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as image_file:
            self.mock_image_response = Response()
            self.mock_image_response.raw = BytesIO(image_file.read())
            self.mock_image_response.status_code = 200

    @property
    def context(self):
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create()

        return {'request': request}

    def test_to_json_ld(self):
        model = self.factory.create()
        federated_serializer = self.federated_serializer(
            instance=model,
            context=self.context
        )

        activity_pub_serializer = self.activity_pub_serializer(
            data=federated_serializer.data,
            context=self.context
        )

        self.assertTrue(activity_pub_serializer.is_valid(raise_exception=True))

        do_good_event = activity_pub_serializer.save()

        self.assertEqual(do_good_event.name, model.title)
        self.assertEqual(do_good_event.summary, model.description.html)
        self.assertEqual(do_good_event.sub_event.count(), model.slots.count())

    def test_to_json_ld_already_exists(self):
        model = self.factory.create()
        federated_serializer = self.federated_serializer(
            instance=model,
            context=self.context
        )

        activity_pub_serializer = self.activity_pub_serializer(
            data=federated_serializer.data,
            context=self.context
        )

        self.assertTrue(activity_pub_serializer.is_valid(raise_exception=True))

        do_good_event = activity_pub_serializer.save()

        self.activity_pub_serializer(instance=do_good_event, data=federated_serializer.data, context=self.context)
        self.assertTrue(activity_pub_serializer.is_valid(raise_exception=True))
        do_good_event = activity_pub_serializer.save()

        self.assertEqual(do_good_event.name, model.title)
        self.assertEqual(do_good_event.summary, model.description.html)
        self.assertEqual(do_good_event.sub_event.count(), model.slots.count())

    def test_to_federated_activity(self):
        activity_pub_model = self.activity_pub_factory.create(iri='http://example.com')

        federated_serializer = self.activity_pub_serializer(
            instance=activity_pub_model, context=self.context
        )
        serializer = self.federated_serializer(
            data=federated_serializer.data, context=self.context
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))

        with mock.patch('requests.get', return_value=self.mock_image_response):
            activity = serializer.save()

        self.assertEqual(activity.title, activity_pub_model.name)
        self.assertEqual(activity.description.html, activity_pub_model.summary)
        self.assertEqual(activity.slots.count(), activity_pub_model.sub_event.count())

    def test_to_federated_activity_already_exists(self):
        activity_pub_model = self.activity_pub_factory.create(iri='http://example.com')

        federated_serializer = self.activity_pub_serializer(
            instance=activity_pub_model, context=self.context
        )

        serializer = self.federated_serializer(
            data=federated_serializer.data, context=self.context
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))

        with mock.patch('requests.get', return_value=self.mock_image_response):
            activity = serializer.save()

        serializer = self.federated_serializer(
            instance=activity, data=federated_serializer.data, context=self.context
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))

        with mock.patch('requests.get', return_value=self.mock_image_response):
            activity = serializer.save()

        self.assertEqual(activity.title, activity_pub_model.name)
        self.assertEqual(activity.description.html, activity_pub_model.summary)
        self.assertEqual(activity.slots.count(), activity_pub_model.sub_event.count())

    def test_url_field_included_when_set(self):
        """Test that url field is included in serialized output when it's set."""
        do_good_event = self.activity_pub_factory.create(
            url='https://example.com/activity'
        )
        serializer = self.activity_pub_serializer(
            instance=do_good_event, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertEqual(data['url'], 'https://example.com/activity')

    def test_url_field_included_when_none(self):
        """Test that url field is included in serialized output even when it's None."""
        do_good_event = self.activity_pub_factory.create(url=None)
        serializer = self.activity_pub_serializer(
            instance=do_good_event, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertIsNone(data['url'])


class GoodDeedSerializerTest(BluebottleTestCase):
    serializer_class = GoodDeedSerializer

    @property
    def context(self):
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create()
        return {'request': request}

    def test_url_field_included_when_set(self):
        """Test that url field is included in GoodDeedSerializer when it's set."""
        good_deed = GoodDeed.objects.create(
            name='Test Good Deed',
            summary='Test summary',
            url='https://example.com/good-deed'
        )

        serializer = self.serializer_class(
            instance=good_deed, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertEqual(data['url'], 'https://example.com/good-deed')

    def test_url_field_included_when_none(self):
        """Test that url field is included in GoodDeedSerializer even when it's None."""
        good_deed = GoodDeed.objects.create(
            name='Test Good Deed',
            summary='Test summary',
            url=None
        )

        serializer = self.serializer_class(
            instance=good_deed, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertIsNone(data['url'])


class CrowdFundingSerializerTest(BluebottleTestCase):
    serializer_class = CrowdFundingSerializer

    @property
    def context(self):
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create()
        return {'request': request}

    def test_url_field_included_when_set(self):
        """Test that url field is included in CrowdFundingSerializer when it's set."""
        crowd_funding = CrowdFunding.objects.create(
            name='Test Crowd Funding',
            summary='Test summary',
            url='https://example.com/crowd-funding',
            target=1000.00,
            target_currency='EUR'
        )

        serializer = self.serializer_class(
            instance=crowd_funding, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertEqual(data['url'], 'https://example.com/crowd-funding')

    def test_url_field_included_when_none(self):
        """Test that url field is included in CrowdFundingSerializer even when it's None."""
        crowd_funding = CrowdFunding.objects.create(
            name='Test Crowd Funding',
            summary='Test summary',
            url=None,
            target=1000.00,
            target_currency='EUR'
        )

        serializer = self.serializer_class(
            instance=crowd_funding, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertIsNone(data['url'])


class OrganizationSerializerTestCase(BluebottleTestCase):
    def setUp(self):
        self.model = OrganizationFactory.create()

        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as f:
            image = File(f)

            self.model.logo = image
            self.model.save()

    def test_data(self):
        serializer = OrganizationSerializer(instance=self.model)

        data = serializer.data

        resource = Resource.from_document(data)
        resource.icon.save()

        resource.save()

        print(
            resource.inbox,
            resource.outbox,
            resource.public_key,
            resource.public_key.private_key
        )

        resource.name = 'some title'
        resource.save()

        resource = Resource.from_iri(resource.iri)
        print(resource.title, resource.icon.url)
