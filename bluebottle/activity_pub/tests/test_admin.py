import mock
from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage

from bluebottle.activity_pub.admin import FollowAdmin, FollowForm
from bluebottle.activity_pub.models import Follow, Person
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class MockSuperUser:
    def has_perm(self, perm):
        return True


class FollowAdminTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.admin = FollowAdmin(Follow, self.site)

        # Create a user and person
        self.user = BlueBottleUserFactory.create(is_staff=True, is_superuser=True)
        self.person = Person.objects.from_model(self.user)

        # Mock the adapter
        self.adapter_mock = mock.patch('bluebottle.activity_pub.adapters.JSONLDAdapter')
        self.adapter_mock.start()

        # Mock the sync method to return a Person
        from bluebottle.activity_pub.adapters import adapter
        adapter.sync = mock.MagicMock(return_value=self.person)
        adapter.publish = mock.MagicMock()

    def tearDown(self):
        self.adapter_mock.stop()

    def test_follow_form(self):
        form = FollowForm(data={'url': 'https://example.com/person/1'})
        self.assertTrue(form.is_valid())

    def test_save_model(self):
        # Create a request
        request = self.factory.post('/admin/activity_pub/follow/add/')
        request.user = self.user

        # Add messages support to request
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # Create a form with valid data
        form = FollowForm(data={'url': 'https://example.com/person/1'})
        form.is_valid()

        # Call save_model
        obj = Follow()
        self.admin.save_model(request, obj, form, False)

        # Check that a Follow object was created
        self.assertEqual(Follow.objects.count(), 1)
        follow = Follow.objects.first()
        self.assertEqual(follow.actor, self.person)
        self.assertEqual(follow.object, self.person)

        # Check that publish was called
        from bluebottle.activity_pub.adapters import adapter
        adapter.publish.assert_called_once_with(follow)
