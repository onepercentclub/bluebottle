from collections import namedtuple
from django.db import connection


class LocalTenant(object):
    def __init__(self, tenant):
        self.tenant = tenant

    def __enter__(self):
        from bluebottle.clients import properties
        if self.tenant:
            properties.set_tenant(self.tenant)

    def __exit__(self, type, value, traceback):
        from bluebottle.clients import properties
        if self.tenant:
            del properties.tenant
            del properties.tenant_properties


def tenant_url():
    # workaround for development setups. Assume port 8000
    domain = connection.tenant.domain_url

    if domain.endswith("localhost"):
        return "http://{0}:8000".format(domain)
    return "https://{0}".format(domain)

def tenant_name():
    return connection.tenant.name

def tenant_site():
    """ somewhat simulates the old 'Site' object """
    return namedtuple('Site', ['name', 'domain'])(tenant_name(),
                                                  connection.tenant.domain_url)
