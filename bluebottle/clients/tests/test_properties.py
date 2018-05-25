import mock

from django.test import TestCase

from bluebottle.clients import TenantProperties
from bluebottle.clients.middleware import properties

Mock = mock.Mock


class TestProperties(TestCase):
    def test_property_match(self):
        """ A match found in the client properties """
        with mock.patch("bluebottle.clients.middleware.settings", foo=1):
            p = TenantProperties()
            p.tenant_properties = {'foo': 2}

            self.failUnless(p.foo == 2)
            self.failUnless(hasattr(p, 'foo'))

    def test_settings_match(self):
        """ No match in properties but match in settings """
        with mock.patch("bluebottle.clients.middleware.settings", foo=1):
            p = TenantProperties()

            self.failUnless(p.foo == 1)
            self.failUnless(hasattr(p, 'foo'))

    def test_nomatch(self):
        """ No match in either properties or settings """
        with mock.patch("bluebottle.clients.middleware.settings", Mock(spec_set=[])):
            p = TenantProperties()
            with self.assertRaises(AttributeError):
                p.foo == 1
            self.failIf(hasattr(p, 'foo'))

    def test_verify_settings(self):
        with mock.patch("bluebottle.clients.middleware.settings",
                        MULTI_TENANT_DIR='/tmp/') as settings, \
                mock.patch("__builtin__.execfile") as execfile:
            properties.set_tenant(Mock(client_name='testtenant'))
            self.assertEquals(execfile.call_args[0][1]['settings'], settings)
