import mock

from io import BytesIO

from requests import Response

from django.test import RequestFactory

from bluebottle.cms.models import SitePlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.time_based.tests.factories import DateActivityFactory
from bluebottle.activity_pub.serializers.json_ld import DoGoodEventSerializer
from bluebottle.activity_pub.serializers.federated_activities import FederatedDateActivitySerializer
from bluebottle.activity_pub.tests.factories import (
    DoGoodEventFactory
)


class DoGoodEventSerializer(BluebottleTestCase):
    activity_pub_serializer = DoGoodEventSerializer
    federated_serializer = FederatedDateActivitySerializer
    factory = DateActivityFactory
    activity_pub_factory = DoGoodEventFactory

    def setUp(self):
        self.settings = SitePlatformSettings.objects.create(
            share_activities=True
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
