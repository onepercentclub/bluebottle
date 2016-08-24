from collections import namedtuple
import re

from django.db import connection
from django.conf import settings
from django.utils.translation import get_language

from djmoney_rates.utils import get_rate

from bluebottle.clients import properties
from tenant_extras.utils import get_tenant_properties


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

def get_public_properties(request):
    """

        Dynamically populate a tenant context with exposed tenant specific properties
        from reef/clients/client_name/properties.py.

        The context processor looks in tenant settings for the uppercased variable names that are defined in
        "EXPOSED_TENANT_PROPERTIES" to generate the context.

        Example:

        EXPOSED_TENANT_PROPERTIES = ['mixpanel', 'analytics']

        This adds the value of the keys MIXPANEL and ANALYTICS from the settings file.

    """

    config = {}

    properties = get_tenant_properties()

    props = None

    try:
        props = getattr(properties, 'EXPOSED_TENANT_PROPERTIES')
    except AttributeError:
        pass

    if not props:
        try:
            props = getattr(settings, 'EXPOSED_TENANT_PROPERTIES')
        except AttributeError:
            return config

    # First load tenant settings that should always be exposed
    if connection.tenant:
        current_tenant = connection.tenant
        properties = get_tenant_properties()
        currencies = properties.CURRENCIES_ENABLED

        for currency in currencies:
            currency['rate'] = get_rate(currency['code'])

        config = {
            'mediaUrl': getattr(properties, 'MEDIA_URL'),
            'defaultAvatarUrl': "/images/default-avatar.png",
            'currencies': currencies,
            'logoUrl': "/images/logo.svg",
            'mapsApiKey': getattr(properties, 'MAPS_API_KEY', ''),
            'donationsEnabled': getattr(properties, 'DONATIONS_ENABLED', True),
            'recurringDonationsEnabled': getattr(properties, 'RECURRING_DONATIONS_ENABLED', False),
            'siteName': current_tenant.name,
            'languages': [{'code': lang[0], 'name': lang[1]} for lang in getattr(properties, 'LANGUAGES')],
            'languageCode': get_language()
        }
        try:
            config['readOnlyFields'] = {
                'user': properties.TOKEN_AUTH.get('assertion_mapping', {}).keys()
            }
        except AttributeError:
            pass

    else:
        config = {}

    # Now load the tenant specific properties
    for item in props:
        try:
            key = re.sub('_.',lambda x: x.group()[1].upper(), item)
            # Use camelcase for setting keys (convert from snakecase)
            config[key] = getattr(properties, item.upper())
        except AttributeError:
            pass

    return config
