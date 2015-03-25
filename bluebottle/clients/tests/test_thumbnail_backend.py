from django.test import TestCase
import mock
from ..thumbnail_backend import TenantThumbnailBackend


class TestTenantThumbnailBackend(TestCase):
    def test_different_tenants(self):
        """ different tenants should get different cached entries """
        backend = TenantThumbnailBackend()
        source = mock.Mock(key="foo.jpg")

        with mock.patch("bluebottle.clients.utils.connection.tenant",
                       mock.Mock(client_name="tenant_a")):
            tenant_a_thumb = backend._get_thumbnail_filename(source,
              geometry_string='10x10', options=dict(format='JPEG', something=42))
        with mock.patch("bluebottle.clients.utils.connection.tenant",
                       mock.Mock(client_name="tenant_b")):
            tenant_b_thumb = backend._get_thumbnail_filename(source,
              geometry_string='10x10', options=dict(format='JPEG', something=42))

        self.assertNotEquals(tenant_a_thumb, tenant_b_thumb)

    def test_no_tenant(self):
        """ make sure everything works if there is no tenant """
        backend = TenantThumbnailBackend()
        source = mock.Mock(key="foo.jpg")

        no_tenant_thumb = backend._get_thumbnail_filename(source,
              geometry_string='10x10', options=dict(format='JPEG', something=42))

        self.failUnless(no_tenant_thumb)
