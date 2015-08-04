from collections import namedtuple
from django.db import connection
from bluebottle.clients import properties
import logging

logger = logging.getLogger()


class LocalTenant(object):
    def __init__(self, tenant=None, clear_tenant=False):
        self.clear_tenant = clear_tenant
        self.previous_tenant = None

        if tenant:
            self.previous_tenant = connection.tenant
            self.tenant = tenant
        else:
            self.tenant = connection.tenant

    def __enter__(self):
        if self.tenant:
            properties.set_tenant(self.tenant)

    def __exit__(self, type, value, traceback):
        if self.clear_tenant:
            try:
                del properties.tenant
                del properties.tenant_properties
            except AttributeError:
                logger.info("Attempted to clear missing tenant properties.")
        elif self.previous_tenant:
            properties.set_tenant(self.previous_tenant)


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
