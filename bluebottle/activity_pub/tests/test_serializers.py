import datetime
from io import BytesIO

import mock
from django.test import RequestFactory
from requests import Response

from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models import GoodDeed, CrowdFunding, GrantApplication, Leave
from bluebottle.activity_pub.serializers.federated_activities import FederatedDateActivitySerializer
from bluebottle.activity_pub.serializers.json_ld import (
    DoGoodEventSerializer, GoodDeedSerializer, CrowdFundingSerializer, GrantApplicationSerializer,
    LeaveSerializer
)
from bluebottle.activity_pub.tests.factories import (
    DoGoodEventFactory, OrganizationFactory
)
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DateParticipantFactory,
)


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
        model.capacity = 25
        model.save(update_fields=['capacity'])
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
        self.assertEqual(do_good_event.capacity, 25)

    def test_federated_payload_includes_slot_capacity(self):
        model = self.factory.create()
        slot = model.slots.get()
        slot.capacity = 42
        slot.save(update_fields=['capacity'])
        federated_serializer = self.federated_serializer(
            instance=model,
            context=self.context,
        )
        payload = federated_serializer.data['sub_event']
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]['capacity'], 42)

    def test_to_json_ld_slots_keep_individual_locations(self):
        model = self.factory.create(slots=[])
        first_location = GeolocationFactory.create()
        second_location = GeolocationFactory.create()
        DateActivitySlotFactory.create(activity=model, location=first_location)
        DateActivitySlotFactory.create(activity=model, location=second_location)

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

        serialized_locations = {
            (
                slot.location.latitude,
                slot.location.longitude
            )
            for slot in do_good_event.sub_event.all()
        }
        expected_locations = {
            (first_location.position.x, first_location.position.y),
            (second_location.position.x, second_location.position.y),
        }
        self.assertSetEqual(serialized_locations, expected_locations)

    def test_to_json_ld_uses_slot_participant_count_for_subevent(self):
        model = self.factory.create(slots=[])
        slot = DateActivitySlotFactory.create(activity=model)
        DateParticipantFactory.create(activity=model, slot=slot, status='accepted')
        DateParticipantFactory.create(activity=model, slot=slot, status='succeeded')
        DateParticipantFactory.create(activity=model, slot=slot, status='new')

        federated_serializer = self.federated_serializer(
            instance=model,
            context=self.context,
        )
        activity_pub_serializer = self.activity_pub_serializer(
            data=federated_serializer.data,
            context=self.context,
        )

        self.assertTrue(activity_pub_serializer.is_valid(raise_exception=True))
        do_good_event = activity_pub_serializer.save()
        sub_event = do_good_event.sub_event.first()

        self.assertIsNotNone(sub_event)
        self.assertEqual(sub_event.contributor_count, 2)

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

    def test_update_does_not_mutate_related_date_activity_capacity(self):
        model = self.factory.create()
        model.capacity = 10
        model.save(update_fields=['capacity'])
        adapter.create_or_update_event(model)
        event = model.event
        if not event.iri:
            event.iri = 'https://source.example/events/test-update-capacity'
            event.save(update_fields=['iri'])

        serializer = self.activity_pub_serializer(
            instance=event,
            data={'id': event.iri, 'type': 'DoGoodEvent', 'capacity': 99},
            partial=True,
            context=self.context,
        )
        self.assertTrue(serializer.is_valid(raise_exception=True))
        serializer.save()

        model.refresh_from_db()
        self.assertEqual(model.capacity, 10)

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

    def test_to_federated_activity_adopts_all_subevents_as_slots(self):
        activity_pub_model = DoGoodEventFactory.create(iri='http://example.com', with_subevents=True)
        subs = list(activity_pub_model.sub_event.order_by('start_time', 'id'))
        self.assertGreaterEqual(len(subs), 2)

        # Ensure the subevents are distinguishable by start time so they should
        # produce distinct DateActivitySlot records.
        subs[0].start_time = subs[0].start_time
        subs[0].save(update_fields=['start_time'])
        subs[1].start_time = subs[0].start_time + datetime.timedelta(hours=4)
        subs[1].save(update_fields=['start_time'])

        federated_payload = self.activity_pub_serializer(
            instance=activity_pub_model,
            context=self.context,
        ).data

        serializer = self.federated_serializer(
            data=federated_payload,
            context=self.context,
        )
        self.assertTrue(serializer.is_valid(raise_exception=True))

        with mock.patch('requests.get', return_value=self.mock_image_response):
            activity = serializer.save()

        self.assertEqual(activity.slots.count(), activity_pub_model.sub_event.count())
        slot_starts = set(activity.slots.values_list('start', flat=True))
        expected_starts = set(
            activity_pub_model.sub_event.values_list('start_time', flat=True)
        )
        self.assertSetEqual(slot_starts, expected_starts)

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


class GrantApplicationSerializerTest(BluebottleTestCase):
    serializer_class = GrantApplicationSerializer

    @property
    def context(self):
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create()
        return {'request': request}

    def test_url_field_included_when_set(self):
        """Test that url field is included in GrantApplicationSerializer when it's set."""
        grant_application = GrantApplication.objects.create(
            name='Test Grant Application',
            summary='Test summary',
            url='https://example.com/grant-application',
            target=1000.00,
            target_currency='EUR'
        )

        serializer = self.serializer_class(
            instance=grant_application, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertEqual(data['url'], 'https://example.com/grant-application')

    def test_url_field_included_when_none(self):
        """Test that url field is included in GrantApplicationSerializer even when it's None."""
        grant_application = GrantApplication.objects.create(
            name='Test Grant Application',
            summary='Test summary',
            url=None,
            target=1000.00,
            target_currency='EUR'
        )

        serializer = self.serializer_class(
            instance=grant_application, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertIsNone(data['url'])


class LeaveSerializerTest(BluebottleTestCase):
    @property
    def context(self):
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create()
        return {'request': request}

    def test_leave_serializer_includes_sync_id(self):
        actor = OrganizationFactory.create()
        good_deed = GoodDeed.objects.create(
            name='Source deed',
            summary='Summary',
            organization=actor
        )
        leave = Leave.objects.create(
            actor=actor,
            object=good_deed,
            participant_sync_id='sync-serializer-1',
        )

        serializer = LeaveSerializer(instance=leave, context=self.context)
        data = serializer.data

        self.assertEqual(data['participant_sync_id'], 'sync-serializer-1')
        self.assertNotIn('participant_transition_type', data)
