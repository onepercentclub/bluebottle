from unittest import mock

from bluebottle.geo.permissions import IsConnectedToProfile
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import LocationFactory
from bluebottle.test.utils import BluebottleTestCase


class IsConnectedToProfileTestCase(BluebottleTestCase):
    def setUp(self):
        super(IsConnectedToProfileTestCase, self).setUp()
        self.init_projects()
        self.permission = IsConnectedToProfile()
        self.location = LocationFactory.create()
        self.member = BlueBottleUserFactory.create(location=self.location)
        self.other_user = BlueBottleUserFactory.create()
        self.request = mock.Mock()
        self.view = mock.Mock()

    def test_member_with_matching_location_has_permission(self):
        self.request.user = self.member
        self.assertTrue(
            self.permission.has_object_permission(
                self.request, self.view, self.location,
            )
        )

    def test_other_member_denied(self):
        self.request.user = self.other_user
        self.assertFalse(
            self.permission.has_object_permission(
                self.request, self.view, self.location,
            )
        )

    def test_staff_has_permission(self):
        staff = BlueBottleUserFactory.create(is_staff=True)
        self.request.user = staff
        self.assertTrue(
            self.permission.has_object_permission(
                self.request, self.view, self.location,
            )
        )
