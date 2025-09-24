from datetime import date, timedelta
from unittest import mock

from bluebottle.activity_pub.models import Event, Place
from bluebottle.activity_pub.serializers.json_ld import ActivityEventSerializer, DeedEventSerializer
from bluebottle.activity_pub.services import EventCreationService
from bluebottle.activity_pub.utils import get_platform_actor
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.utils import BluebottleTestCase


class EventCreationServiceTestCase(BluebottleTestCase):
    """Test case for creating Events from Activities using EventCreationService"""

    def setUp(self):
        super().setUp()

        # Create platform organization for get_platform_actor
        self.platform_org = OrganizationFactory.create()
        SitePlatformSettings.objects.create(organization=self.platform_org)

        # Create a user and initiative
        self.user = BlueBottleUserFactory.create()

    def test_create_event_from_deed_basic(self):
        """Test creating a basic Event from a Deed"""
        # Create a deed
        deed = DeedFactory.create(
            owner=self.user,
            title="Beach Cleanup",
            start=date.today() + timedelta(days=7),
            end=date.today() + timedelta(days=8)
        )

        # Serialize the deed to get the data format expected by EventCreationService
        serializer = ActivityEventSerializer(deed)
        data = serializer.data

        # Create event from the deed data
        event = EventCreationService.create_event_from_activity(data)
        event.refresh_from_db()

        # Verify the event was created correctly
        self.assertIsInstance(event, Event)
        self.assertEqual(event.name, deed.title)
        self.assertEqual(event.description, deed.description.html)
        self.assertEqual(event.start.date(), deed.start)
        self.assertEqual(event.end.date(), deed.end)
        self.assertEqual(event.activity_type, 'deed')  # Should be deed type since no duration or subevents
        self.assertEqual(event.organizer, get_platform_actor())
        self.assertIsNone(event.duration)
        self.assertIsNone(event.place)
        self.assertFalse(event.subevents.exists())

    def test_create_event_from_deed_with_place(self):
        """Test creating an Event from a Deed that has location information"""
        # Create a deed with location
        deed = DeedFactory.create(
            owner=self.user,
            title="Community Garden Work",
            start=date.today() + timedelta(days=5),
            end=date.today() + timedelta(days=5)
        )

        # Mock location data that would come from serializer
        location_data = {
            'name': 'Community Garden',
            'street_address': '123 Garden St',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'mapbox_id': 'place.123'
        }

        # Serialize deed and add place data
        serializer = ActivityEventSerializer(deed)
        data = serializer.data
        data['place'] = location_data

        # Create event from deed data with place
        event = EventCreationService.create_event_from_activity(data)
        event.refresh_from_db()

        # Verify event and place were created
        self.assertIsInstance(event, Event)
        self.assertEqual(event.name, deed.title)
        self.assertIsNotNone(event.place)
        self.assertIsInstance(event.place, Place)
        self.assertEqual(event.place.name, location_data['name'])
        self.assertEqual(event.place.street_address, location_data['street_address'])
        self.assertEqual(float(event.place.latitude), location_data['latitude'])
        self.assertEqual(float(event.place.longitude), location_data['longitude'])
        self.assertEqual(event.place.mapbox_id, location_data['mapbox_id'])

    def test_create_event_from_deed_serializer_data(self):
        """Test creating Event using DeedEventSerializer specifically"""
        start = date.today() + timedelta(days=1)
        end = date.today() + timedelta(days=12)
        deed = DeedFactory.create(
            owner=self.user,
            title="Park Restoration",
            start=start,
            end=end
        )

        # Use DeedEventSerializer directly to ensure it works properly
        serializer = DeedEventSerializer(deed)
        data = serializer.data

        # Verify we get the expected data structure
        self.assertEqual(data['name'], deed.title)
        self.assertEqual(data['description'], deed.description.html)

        # For date fields, the serializer converts dates to ISO datetime strings
        # We need to parse them back to compare with the original dates
        from datetime import datetime
        start_datetime = datetime.fromisoformat(data['start'])
        end_datetime = datetime.fromisoformat(data['end'])

        self.assertEqual(start_datetime.date(), deed.start)
        self.assertEqual(end_datetime.date(), deed.end)

        # Create event from serialized data
        event = EventCreationService.create_event_from_activity(data)
        event.refresh_from_db()

        # Verify event creation
        self.assertIsInstance(event, Event)
        self.assertEqual(event.name, deed.title)
        self.assertEqual(event.description, deed.description.html)
        self.assertEqual(event.start.date(), deed.start)
        self.assertEqual(event.end.date(), deed.end)
        self.assertEqual(event.activity_type, 'deed')

    def test_create_event_handles_resourcetype_removal(self):
        """Test that EventCreationService properly removes resourcetype from data"""
        deed = DeedFactory.create(
            owner=self.user,
            title="Tree Planting",
        )

        serializer = ActivityEventSerializer(deed)
        data = serializer.data

        # Add resourcetype which should be removed
        data['resourcetype'] = 'activities/deeds'

        # Create event - should not fail even with resourcetype present
        event = EventCreationService.create_event_from_activity(data)
        event.refresh_from_db()

        # Verify event was created successfully
        self.assertIsInstance(event, Event)
        self.assertEqual(event.name, deed.title)

    def test_create_event_no_subevents_for_deed(self):
        """Test that Deeds don't create subevents (unlike DateActivities)"""
        deed = DeedFactory.create(
            owner=self.user,
            title="River Cleanup",
        )

        serializer = ActivityEventSerializer(deed)
        data = serializer.data

        # Verify no subevents in data
        self.assertNotIn('subevents', data)

        # Create event
        event = EventCreationService.create_event_from_activity(data)
        event.refresh_from_db()

        # Verify no subevents were created
        self.assertFalse(event.subevents.exists())
        self.assertEqual(event.activity_type, 'deed')

    def test_create_event_with_platform_actor(self):
        """Test that Event is created with the correct platform actor as organizer"""
        deed = DeedFactory.create(
            owner=self.user,
            title="Wildlife Conservation",
        )

        serializer = ActivityEventSerializer(deed)
        data = serializer.data

        # Get platform actor before creating event
        platform_actor = get_platform_actor()
        self.assertIsNotNone(platform_actor)

        # Create event
        event = EventCreationService.create_event_from_activity(data)
        event.refresh_from_db()

        # Verify organizer is set to platform actor
        self.assertEqual(event.organizer, platform_actor)

    def test_create_event_handles_empty_place_data(self):
        """Test that EventCreationService handles place data properly when empty"""
        deed = DeedFactory.create(
            owner=self.user,
            title="Online Coordination",
        )

        serializer = ActivityEventSerializer(deed)
        data = serializer.data

        # Add empty place data
        data['place'] = None

        # Create event
        event = EventCreationService.create_event_from_activity(data)
        event.refresh_from_db()

        # Verify event was created without place
        self.assertIsInstance(event, Event)
        self.assertIsNone(event.place)

    def test_create_event_transaction_rollback_on_error(self):
        """Test that Event creation is rolled back on error due to @transaction.atomic"""
        deed = DeedFactory.create(
            owner=self.user,
            title="Disaster Relief",
        )

        serializer = ActivityEventSerializer(deed)
        data = serializer.data

        # Count events before
        initial_event_count = Event.objects.count()

        # Mock Event.objects.create to raise an exception
        with mock.patch('bluebottle.activity_pub.models.Event.objects.create') as mock_create:
            mock_create.side_effect = Exception("Database error")

            # Attempt to create event - should raise exception
            with self.assertRaises(Exception):
                EventCreationService.create_event_from_activity(data)

        # Verify no events were created due to transaction rollback
        self.assertEqual(Event.objects.count(), initial_event_count)

    def test_polymorphic_serializer_selects_deed_serializer(self):
        """Test that ActivityEventSerializer correctly selects DeedEventSerializer for Deed models"""
        deed = DeedFactory.create(
            owner=self.user,
            title="Food Drive",
        )

        # Test that polymorphic serializer selects correct serializer for Deed
        serializer = ActivityEventSerializer(deed)

        # The data should be formatted by DeedEventSerializer
        data = serializer.data
        self.assertIn('start', data)
        self.assertIn('end', data)
        self.assertNotIn('duration', data)  # Duration is not in DeedEventSerializer
        self.assertNotIn('subevents', data)  # Subevents are not in DeedEventSerializer
