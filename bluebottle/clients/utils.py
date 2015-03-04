from collections import namedtuple
from django.db import connection

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
