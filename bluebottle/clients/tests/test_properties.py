import mock

from django.test import TestCase

from bluebottle.clients.middleware import TenantProperties, TenantPropertiesMiddleware
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


class TestTenantMiddleware(TestCase):
    def setUp(self):
        self.middleware = TenantPropertiesMiddleware()

    def test_no_tenant(self):
        """ verify that ordinary settings resolving just works """
        with mock.patch("bluebottle.clients.middleware.settings", foo=42):
            self.middleware.process_request(Mock())
            self.assertEquals(properties.foo, 42)

    def test_invalid_tenant(self):
        """ verify that with an invalid tenant default settings resolving
            works """
        with mock.patch("bluebottle.clients.middleware.settings", foo=42), \
                mock.patch("bluebottle.clients.middleware.connection", Mock(**{"tenant.client_name": "dontexist"})):
            self.middleware.process_request(Mock())
            self.assertEquals(properties.foo, 42)

    def test_valid_tenant(self):
        """ verify that the correct properties are loaded"""
        with mock.patch("bluebottle.clients.middleware.settings", MULTI_TENANT_DIR="/some/client/path/"), \
                mock.patch("bluebottle.clients.middleware.connection", Mock(**{"tenant.client_name": "valid"})), \
                mock.patch("__builtin__.execfile") as execfile:
            self.middleware.process_request(Mock())
            self.assertEquals(execfile.call_args_list[0][0][0], "/some/client/path/valid/settings.py")
