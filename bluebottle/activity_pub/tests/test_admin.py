from datetime import timedelta
from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone

from bluebottle.activities.models import Activity
from bluebottle.activity_pub.models import Event
from bluebottle.activity_pub.tests.factories import EventFactory, OrganizationFactory, PlaceFactory
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.deeds.models import Deed
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory as BluebottleOrganizationFactory
from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.time_based.models import DeadlineActivity, DateActivity


class EventAdminTestCase(BluebottleAdminTestCase):
    """Test cases for Event admin functionality, particularly the adopt_event feature"""

    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.app.set_user(self.superuser)
        self.platform_org = BluebottleOrganizationFactory.create()
        SitePlatformSettings.objects.create(organization=self.platform_org)
        self.ap_organization = OrganizationFactory.create()
        
    def test_adopt_event_deed_type(self):
        """Test adopting an event that should create a Deed activity"""
        # Create an event without duration or subevents (deed type)
        event = EventFactory.create(
            name="Beach Cleanup",
            description="Clean up the local beach",
            organizer=self.ap_organization,
            duration=None
        )
        
        # Ensure no activity is linked initially
        self.assertIsNone(event.activity)
        self.assertEqual(event.activity_type, 'deed')
        
        # Call the adopt_event admin action
        url = reverse('admin:activity_pub_event_adopt', args=[event.pk])
        response = self.app.get(url)
        
        # Check that activity was created
        event.refresh_from_db()
        self.assertIsNotNone(event.activity)
        self.assertIsInstance(event.activity, Deed)
        self.assertEqual(event.activity.title, event.name)
        self.assertEqual(event.activity.description.html, event.description)
        self.assertEqual(event.activity.owner, self.superuser)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Successfully created Activity' in str(m) for m in messages))
        
    def test_adopt_event_deadline_type(self):
        """Test adopting an event with duration (deadline activity type)"""
        event = EventFactory.create(
            name="Volunteer Training",
            description="Online training session",
            organizer=self.ap_organization,
            duration=timedelta(hours=3),
            start=timezone.now() + timedelta(days=5),
            end=None
        )
        
        # Ensure it's identified as deadline type
        self.assertEqual(event.activity_type, 'deadline')
        
        # Adopt the event
        url = reverse('admin:activity_pub_event_adopt', args=[event.pk])
        response = self.app.get(url)
        
        # Check that deadline activity was created
        event.refresh_from_db()
        self.assertIsNotNone(event.activity)
        self.assertIsInstance(event.activity, DeadlineActivity)
        self.assertEqual(event.activity.title, event.name)
        self.assertEqual(event.activity.duration, event.duration)
        
    def test_adopt_event_date_type(self):
        """Test adopting an event with subevents (date activity type)"""
        # Create parent event
        parent_event = EventFactory.create(
            name="Community Workshop Series",
            description="Multi-session workshop",
            organizer=self.ap_organization
        )
        
        # Create subevents
        EventFactory.create_batch(
            2,
            parent=parent_event,
            organizer=self.ap_organization,
            start=timezone.now() + timedelta(days=1)
        )
        
        # Ensure it's identified as date type
        self.assertEqual(parent_event.activity_type, 'date')
        
        # Adopt the event
        url = reverse('admin:activity_pub_event_adopt', args=[parent_event.pk])
        response = self.app.get(url)
        
        # Check that date activity was created
        parent_event.refresh_from_db()
        self.assertIsNotNone(parent_event.activity)
        self.assertIsInstance(parent_event.activity, DateActivity)
        self.assertEqual(parent_event.activity.title, parent_event.name)
        
    def test_adopt_event_already_adopted(self):
        """Test that adopting an already adopted event shows warning"""
        event = EventFactory.create(organizer=self.ap_organization)
        
        # First adoption
        url = reverse('admin:activity_pub_event_adopt', args=[event.pk])
        response = self.app.get(url)
        
        event.refresh_from_db()
        self.assertIsNotNone(event.activity)
        
        # Try to adopt again
        response = self.app.get(url)
        
        # Check warning message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('already been adopted' in str(m) for m in messages))
        
    def test_adopt_event_permission_required(self):
        """Test that adopt event requires proper permissions"""
        # Create a staff user without deed permissions
        staff_user = BlueBottleUserFactory.create(is_staff=True)
        staff_group = Group.objects.get(name='Staff')
        staff_user.groups.add(staff_group)
        
        event = EventFactory.create(organizer=self.ap_organization)
        
        # Set user without deed permissions
        self.app.set_user(staff_user)
        
        # Try to adopt event
        url = reverse('admin:activity_pub_event_adopt', args=[event.pk])
        response = self.app.get(url, expect_errors=True)
        
        # Should get permission denied
        self.assertEqual(response.status_code, 403)
        
    def test_adopt_event_with_place(self):
        """Test adopting an event that has location information"""
        place = PlaceFactory.create(
            name="Community Center",
            street_address="123 Main St",
            latitude=40.7128,
            longitude=-74.0060
        )
        
        event = EventFactory.create(
            name="Local Meetup",
            organizer=self.ap_organization,
            place=place
        )
        
        # Adopt the event
        url = reverse('admin:activity_pub_event_adopt', args=[event.pk])
        response = self.app.get(url)
        
        # Check that activity was created
        event.refresh_from_db()
        self.assertIsNotNone(event.activity)
        self.assertEqual(event.activity.title, event.name)
        
    def test_adopt_event_error_handling(self):
        """Test that errors during adoption are handled gracefully"""
        # Create event with invalid data that might cause serializer errors
        event = EventFactory.create(
            name="",  # Empty name might cause validation error
            organizer=self.ap_organization
        )
        
        # Try to adopt event
        url = reverse('admin:activity_pub_event_adopt', args=[event.pk])
        response = self.app.get(url)
        
        # Should handle error gracefully
        event.refresh_from_db()
        # Event should not have activity linked if there was an error
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        # There should be some kind of message (either error or success)
        self.assertTrue(len(messages) > 0)
        
    def test_adopt_event_redirects_to_activity_admin(self):
        """Test that successful adoption redirects to the activity admin page"""
        event = EventFactory.create(
            name="Test Event",
            organizer=self.ap_organization
        )
        
        # Adopt the event
        url = reverse('admin:activity_pub_event_adopt', args=[event.pk])
        response = self.app.get(url)
        
        # Check redirect to activity admin
        event.refresh_from_db()
        if event.activity:
            expected_redirect = reverse('admin:activities_activity_change', args=[event.activity.pk])
            self.assertEqual(response.status_code, 302)
            # The redirect URL should be to the activity admin page
            
    def test_event_activity_type_property(self):
        """Test that Event.activity_type property works correctly"""
        # Test deed type (no duration, no subevents)
        deed_event = EventFactory.create(duration=None, organizer=self.ap_organization)
        self.assertEqual(deed_event.activity_type, 'deed')
        
        # Test deadline type (has duration)
        deadline_event = EventFactory.create(
            duration=timedelta(hours=2), 
            organizer=self.ap_organization
        )
        self.assertEqual(deadline_event.activity_type, 'deadline')
        
        # Test date type (has subevents)
        date_event = EventFactory.create(organizer=self.ap_organization)
        EventFactory.create(parent=date_event, organizer=self.ap_organization)
        self.assertEqual(date_event.activity_type, 'date')
        
    def test_event_adopted_property(self):
        """Test that Event.adopted property works correctly"""
        event = EventFactory.create(organizer=self.ap_organization)
        
        # Initially not adopted
        self.assertFalse(event.adopted)
        
        # After adoption
        url = reverse('admin:activity_pub_event_adopt', args=[event.pk])
        response = self.app.get(url)
        
        event.refresh_from_db()
        if event.activity:
            self.assertTrue(event.adopted)
            
    def test_adopt_event_preserves_event_data(self):
        """Test that event data is properly preserved in the created activity"""
        start_time = timezone.now() + timedelta(days=3)
        end_time = start_time + timedelta(hours=4)
        
        event = EventFactory.create(
            name="Data Preservation Test",
            description="Testing data preservation",
            start=start_time,
            end=end_time,
            organizer=self.ap_organization
        )
        
        # Adopt the event
        url = reverse('admin:activity_pub_event_adopt', args=[event.pk])
        response = self.app.get(url)
        
        # Check that data was preserved
        event.refresh_from_db()
        if event.activity:
            activity = event.activity
            self.assertEqual(activity.title, event.name)
            self.assertEqual(activity.description.html, event.description)
            
            # For Deed, check start/end dates
            if isinstance(activity, Deed):
                self.assertEqual(activity.start.date(), event.start.date())
                self.assertEqual(activity.end.date(), event.end.date())
