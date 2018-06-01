from bluebottle.cms.models import SitePlatformSettings
from django.db import connection
from bluebottle.clients import properties


def tenant(request):

    site_settings = SitePlatformSettings.load()

    return {
        'tenant': connection.tenant,
        'properties': properties,
        'logo': site_settings.logo
    }
