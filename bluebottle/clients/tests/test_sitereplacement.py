from django.test import TestCase
import mock
from ..utils import tenant_url, tenant_name, tenant_site


def FixMock(**kwargs):
    """ mock.Mock(name='x') == 'x' is False due to special 'name' behaviour """
    m = mock.Mock(**kwargs)
    if 'name' in kwargs:
        m.name = kwargs['name']
    return m


class TestTenantSiteReplacement(TestCase):
    def test_domain(self):
        with mock.patch("bluebottle.clients.utils.connection.tenant",
                        FixMock(domain_url="example.com")):
            self.assertEquals(tenant_url(), "https://example.com")

    def test_name(self):
        with mock.patch("bluebottle.clients.utils.connection.tenant",
                        FixMock(name="Acme Inc.")):
            self.assertEquals(tenant_name(), "Acme Inc.")

    def test_site(self):
        with mock.patch("bluebottle.clients.utils.connection.tenant",
                        FixMock(domain_url="acme.com", name="Acme Inc.")):
            site = tenant_site()
            self.assertEquals(site.domain, "acme.com")
            self.assertEquals(site.name, "Acme Inc.")
