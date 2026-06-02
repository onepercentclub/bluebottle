from django.test import RequestFactory

from bluebottle.activity_pub.views import ActivityPubPermission, InboxPermission
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.activity_pub.tests.factories import FollowFactory, OrganizationFactory


class PermissionTestCase(BluebottleTestCase):
    def setUp(self):
        self.actor = OrganizationFactory.create(iri='https://example.com')
        self.request_factory = RequestFactory()
        self.permission = self.permission_class()

        super().setUp()

    def authenticate(self, request, actor=None):
        request.auth = self.actor
        return request


class ActivityPubPermissionTestCase(PermissionTestCase):
    permission_class = ActivityPubPermission

    def test_post(self):
        request = self.request_factory.post(path='/', data={'id': 'https://example.com'})

        self.assertFalse(
            self.permission.has_permission(request)
        )

    def test_unsigned_get(self):
        request = self.authenticate(self.request_factory.get(path='/'))
        self.assertTrue(
            self.permission.has_permission(request)
        )

    def test_signed_get(self):
        request = self.authenticate(self.request_factory.get(path='/'), self.actor)

        self.assertTrue(
            self.permission.has_permission(request)
        )

    def test_unsigned_get_closed_platform(self):
        MemberPlatformSettings.objects.create(closed=True)

        request = self.authenticate(self.request_factory.get(path='/'))

        self.assertFalse(
            self.permission.has_permission(request)
        )

    def test_signed_get_closed_platform(self):
        MemberPlatformSettings.objects.create(closed=True)

        request = self.authenticate(self.request_factory.get(path='/'), self.actor)

        self.assertFalse(
            self.permission.has_permission(request)
        )

    def test_signed_get_closed_platform_followed(self):
        MemberPlatformSettings.objects.create(closed=True)
        FollowFactory.create(object=self.actor)

        request = self.authenticate(self.request_factory.get(path='/'), self.actor)

        self.assertTrue(
            self.permission.has_permission(request)
        )


class InboxPermissionTestCase(PermissionTestCase):
    permission_class = InboxPermission

    def request(self, method='POST', data=None, actor=None):
        request = self.request_factory.generic(method, path='/', content_type='application/ld+json')
        request.data = data
        request.auth = actor

        return request

    def test_get(self):
        self.assertTrue(
            self.permission.has_permission(self.request('GET'))
        )

    def test_post_no_data(self):
        self.assertFalse(
            self.permission.has_permission(self.request(data=None))
        )

    def test_post_no_type(self):
        self.assertFalse(
            self.permission.has_permission(self.request(data={}))
        )

    def test_post_follow(self):
        self.assertTrue(
            self.permission.has_permission(self.request(data={'type': 'Follow'}))
        )

    def test_post_accept(self):
        FollowFactory.create(object=self.actor)

        self.assertTrue(
            self.permission.has_permission(self.request(data={'type': 'Create'}, actor=self.actor))
        )

    def test_post_accept_no_follow(self):
        self.assertFalse(
            self.permission.has_permission(self.request(data={'type': 'Create'}, actor=self.actor))
        )

    def test_post_accept_no_auth(self):
        FollowFactory.create(object=self.actor)

        self.assertFalse(
            self.permission.has_permission(self.request(data={'type': 'Create'}))
        )

    def test_post_publish(self):
        FollowFactory.create(object=self.actor)

        self.assertTrue(
            self.permission.has_permission(self.request(data={'type': 'Create'}, actor=self.actor))
        )

    def test_post_publish_no_follow(self):
        self.assertFalse(
            self.permission.has_permission(self.request(data={'type': 'Create'}, actor=self.actor))
        )

    def test_post_publish_no_auth(self):
        FollowFactory.create(object=self.actor)

        self.assertFalse(
            self.permission.has_permission(self.request(data={'type': 'Create'}))
        )
