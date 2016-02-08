import re
import json

from django.db import connection
from django.conf import settings

from bluebottle.clients import properties
from tenant_extras.context_processors import tenant_properties as tenant_extra_properties


def tenant_properties(request):
    extra_properties = tenant_extra_properties(request)
    tenant_settings = json.loads(extra_properties['settings'])


    # If tenant has SAML enabled then we also return a list
    # of read-only user profile properties.
    try:
        mappings = properties.TOKEN_AUTH['assertion_mapping']
        tenant_settings['readOnlyFields'] = {
            'user': mappings.keys()
        }

        extra_properties['settings'] = json.dumps(tenant_settings)
    except KeyError:
        pass
    except AttributeError:
        pass

    static_url = getattr(settings, 'STATIC_URL')

    extra_properties['TENANT_STATIC_PATH'] = "{0}frontend/{1}/".format(static_url,
                                                                       connection.tenant.client_name)
    extra_properties['STATIC_PATH'] = "{0}frontend/".format(static_url)
    extra_properties['GIT_COMMIT'] = getattr(settings, 'GIT_COMMIT', 'dummy')
    return extra_properties


def sentry_dsn(request):
    """
    Make the Sentry / Raven DSN available in the templates *without* the secret key.
    """
    try:
        raven_config = settings.RAVEN_CONFIG['dsn']
    except AttributeError:
        return {}
    except KeyError:
        return {}

    match = re.search(
        r"https:\/\/([a-z|0-9]+):([a-z|0-9]+)\@app.getsentry.com\/(\d+)",
        raven_config, re.M | re.I)

    if not match:
        return {}
    else:
        public_key = match.group(1)
        project_id = match.group(3)

        return {
            'RAVEN_DSN': "https://{0}@app.getsentry.com/{1}".format(public_key,
                                                                    project_id)}


def tenant(request):
    """
    Add tenant to request context
    """
    if connection.tenant:
        tenant = connection.tenant
        return {
            'TENANT': connection,
            'TENANT_LANGUAGE': '{0}{1}'.format(tenant.client_name,
                                               request.LANGUAGE_CODE)
        }
    return {}
