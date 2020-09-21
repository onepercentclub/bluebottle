import mock
import os

from django.test import TestCase

from bluebottle.clients import TenantProperties
from bluebottle.clients import properties

Mock = mock.Mock


class TestProperties(TestCase):
    def test_property_match(self):
        """ A match found in the client properties """
        with mock.patch("bluebottle.clients.settings", foo=1):
            p = TenantProperties()
            p.tenant_properties = {'foo': 2}

            self.failUnless(p.foo == 2)
            self.failUnless(hasattr(p, 'foo'))

    def test_settings_match(self):
        """ No match in properties but match in settings """
        with mock.patch("bluebottle.clients.settings", foo=1):
            p = TenantProperties()

            self.failUnless(p.foo == 1)
            self.failUnless(hasattr(p, 'foo'))

    def test_nomatch(self):
        """ No match in either properties or settings """
        with mock.patch("bluebottle.clients.settings", Mock(spec_set=[])):
            p = TenantProperties()
            with self.assertRaises(AttributeError):
                p.foo == 1
            self.failIf(hasattr(p, 'foo'))

    def test_verify_settings(self):
        tenant_dir = os.path.join(os.path.dirname(__file__), 'files/')
        with mock.patch("bluebottle.clients.settings", MULTI_TENANT_DIR=tenant_dir):
            properties.set_tenant(Mock(client_name='testtenant'))
            self.assertEqual(properties.set_by_test, True)
