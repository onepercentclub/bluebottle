from django.contrib.auth.models import AnonymousUser, Permission, Group

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class AnonymousAuthenticationBackendTest(BluebottleTestCase):
    def setUp(self):
        super(AnonymousAuthenticationBackendTest, self).setUp()

        self.codename = 'add_site'
        self.permission_string = 'sites.{}'.format(self.codename)

        self.permission = Permission.objects.get(codename=self.codename)
        self.group = Group.objects.create(name='Anonymous')

        self.anonymous_user = AnonymousUser()
        self.user = BlueBottleUserFactory.create()

    def test_has_permission(self):
        """ Test that anonymous user get permissions from anonymous group"""
        self.group.permissions.add(self.permission)
        self.assertTrue(self.anonymous_user.has_perm(self.permission_string))

    def test_has_no_permission(self):
        """ Test that anonymous user get no permissions if permission not in group"""
        self.assertFalse(self.anonymous_user.has_perm(self.permission_string))

    def test_authenticated_user_has_no_permission(self):
        """ Test that normal user get no permissions"""
        self.group.permissions.add(self.permission)

        self.assertFalse(self.user.has_perm(self.permission_string))

    def test_no_permission_non_existant_group(self):
        """ Test that if the group does not exist, the user does not get the permission"""
        self.group.delete()

        self.assertFalse(self.anonymous_user.has_perm(self.permission_string))
