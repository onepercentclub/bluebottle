from bluebottle.cms.models import SitePlatformSettings
from django.db import connection


def tenant(request):

    site_settings = SitePlatformSettings.load()

    return {
        'tenant': connection.tenant,
        'logo': site_settings.logo
    }
