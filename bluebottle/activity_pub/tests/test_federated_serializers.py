from datetime import datetime
from io import BytesIO

import httmock
from django.test import RequestFactory
from requests import Response

from bluebottle.cms.models import SitePlatformSettings

from bluebottle.activity_pub.renderers import JSONLDRenderer
from bluebottle.activity_pub.models import Event
from bluebottle.activity_pub.serializers.base import (
    ActivityPubSerializer, FederatedObjectSerializer
)

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, DeadlineActivityFactory,
    ScheduleActivityFactory, PeriodicActivityFactory
)

from bluebottle.test.factory_models.organizations import OrganizationFactory as BlueobttoeOrganizationFactory
from bluebottle.activity_pub.tests.factories import (
    OrganizationFactory, PersonFactory, GoodDeedFactory, CreateFactory, FollowFactory,
    CrowdFundingFactory, DoGoodEventFactory, SubEventFactory
)

from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.funding.tests.factories import FundingFactory


@httmock.urlmatch(path=r'^/image/1')
def image_mock(url, request):
    with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as image_file:
        mock_response = Response()
        mock_response.raw = BytesIO(image_file.read())
        mock_response.status_code = 200

    return mock_response


class FederatedSerializerTestCase:
    factory_data = {}

    def setUp(self):
        self.renderer = JSONLDRenderer()

        site_settings = SitePlatformSettings.load()
        site_settings.share_activities = ['supplier', 'consumer']
        site_settings.save()

    @property
    def context(self):
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create()

        return {'request': request}

    def test_to_representation(self):
        self.instance = self.factory.create()
        self.serializer = FederatedObjectSerializer(
            instance=self.instance, context=self.context
        )

    def test_create_activity_pub_resource(self):
        self.instance = self.factory.create()
        serializer = FederatedObjectSerializer(
            instance=self.instance, context=self.context
        )

        activity_pub_serializer = ActivityPubSerializer(
            data=serializer.data
        )
        self.assertTrue(activity_pub_serializer.is_valid())

        activity_pub_serializer.save(federated_object=self.instance)
        self.activity_pub_instance = activity_pub_serializer.instance

        self.assertEqual(self.instance, self.activity_pub_instance.federated_object)
        self.assertTrue(
            isinstance(self.activity_pub_instance, self.activity_pub_factory._meta.model)
        )

    def create(self):
        self.activity_pub_instance = self.activity_pub_factory.create(
            iri='http://exampl.com/id/1',
            **self.factory_data
        )

    def test_create_federated_model(self):
        follow = FollowFactory.create(
            default_owner=BlueBottleUserFactory.create()
        )
        self.create()

        if isinstance(self.activity_pub_instance, Event):
            CreateFactory.create(
                object=self.activity_pub_instance, actor=follow.object
            )

        serializer = ActivityPubSerializer(
            instance=self.activity_pub_instance, context=self.context
        )

        federated_serializer = FederatedObjectSerializer(
            data=serializer.data
        )
        self.assertTrue(federated_serializer.is_valid())

        with httmock.HTTMock(image_mock):
            federated_serializer.save()

        self.instance = federated_serializer.instance
        self.instance.refresh_from_db()

        self.assertEqual(
            self.instance.origin, self.activity_pub_instance
        )

        self.assertTrue(
            isinstance(self.instance, self.factory._meta.model)
        )


class OrganizationSerializerTestCase(FederatedSerializerTestCase, BluebottleTestCase):
    factory = BlueobttoeOrganizationFactory
    activity_pub_factory = OrganizationFactory

    def test_to_representation(self):
        super().test_to_representation()

        self.assertEqual(
            self.instance.name, self.serializer.data['name']
        )

    def test_create_activity_pub_resource(self):
        super().test_create_activity_pub_resource()

        self.assertEqual(
            self.instance.name, self.activity_pub_instance.name
        )


class PersonSerializerTestCase(FederatedSerializerTestCase, BluebottleTestCase):
    factory = BlueBottleUserFactory
    activity_pub_factory = PersonFactory

    def test_to_representation(self):
        super().test_to_representation()

        self.assertEqual(
            self.instance.first_name, self.serializer.data['given_name']
        )
        self.assertEqual(
            self.instance.last_name, self.serializer.data['family_name']
        )
        self.assertEqual(
            self.instance.full_name, self.serializer.data['name']
        )

    def test_create_activity_pub_resource(self):
        super().test_create_activity_pub_resource()

        self.assertEqual(
            self.instance.first_name, self.activity_pub_instance.given_name
        )
        self.assertEqual(
            self.instance.first_name, self.activity_pub_instance.family_name
        )
        self.assertEqual(
            self.instance.full_name, self.activity_pub_instance.name
        )


class GoodDeedSerializerTestCase(FederatedSerializerTestCase, BluebottleTestCase):
    factory = DeedFactory
    activity_pub_factory = GoodDeedFactory

    def test_to_representation(self):
        super().test_to_representation()

        self.assertEqual(
            self.instance.title, self.serializer.data['name']
        )
        self.assertEqual(
            self.instance.description.html, self.serializer.data['summary']
        )
        self.assertEqual(
            self.instance.start, self.serializer.data['start_time'].date()
        )
        self.assertEqual(
            self.instance.end, self.serializer.data['end_time'].date()
        )

    def test_create_activity_pub_resource(self):
        super().test_create_activity_pub_resource()

        self.assertEqual(
            self.instance.title, self.activity_pub_instance.name
        )
        self.assertEqual(
            self.instance.description.html, self.activity_pub_instance.summary
        )


class CrowdFundingSerializerTestCase(FederatedSerializerTestCase, BluebottleTestCase):
    factory = FundingFactory
    activity_pub_factory = CrowdFundingFactory

    def test_to_representation(self):
        super().test_to_representation()

        self.assertEqual(
            self.instance.title, self.serializer.data['name']
        )
        self.assertEqual(
            self.instance.description.html, self.serializer.data['summary']
        )
        self.assertEqual(
            self.instance.deadline, datetime.fromisoformat(self.serializer.data['end_time'])
        )
        self.assertEqual(
            self.instance.target.amount, float(self.serializer.data['target'])
        )
        self.assertEqual(
            str(self.instance.target.currency), self.serializer.data['target_currency']
        )

    def test_create_activity_pub_resource(self):
        super().test_create_activity_pub_resource()

        self.assertEqual(
            self.instance.title, self.activity_pub_instance.name
        )
        self.assertEqual(
            self.instance.description.html, self.activity_pub_instance.summary
        )


class DeadlineSerializerTestCase(FederatedSerializerTestCase, BluebottleTestCase):
    factory = DeadlineActivityFactory
    activity_pub_factory = DoGoodEventFactory

    factory_data = {
        'slot_mode': None,
        'join_mode': None,
        'event_attendance_mode': 'online'
    }


class DateSerializerTestCase(FederatedSerializerTestCase, BluebottleTestCase):
    factory = DateActivityFactory
    activity_pub_factory = DoGoodEventFactory

    def create(self):
        super().create()
        SubEventFactory.create(
            parent=self.activity_pub_instance,
            event_attendance_mode='online',
        )

    factory_data = {
        'event_attendance_mode': 'online',
        'slot_mode': None,
        'join_mode': None,
    }


class ScheduleSerializerTestCase(FederatedSerializerTestCase, BluebottleTestCase):
    factory = ScheduleActivityFactory
    activity_pub_factory = DoGoodEventFactory
    factory_data = {
        'event_attendance_mode': 'online',
        'slot_mode': 'ScheduledSlotMode'
    }


class PeriodicSerializerTestCase(FederatedSerializerTestCase, BluebottleTestCase):
    factory = PeriodicActivityFactory
    activity_pub_factory = DoGoodEventFactory

    factory_data = {
        'slot_mode': 'PeriodicSlotMode',
        'event_attendance_mode': 'online'
    }
