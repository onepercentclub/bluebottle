from bluebottle.cms.models import SitePlatformSettings
from django.db import connection


def tenant(request):

    logo = SitePlatformSettings.load().logo

    return {
        'tenant': connection.tenant,
        'logo': logo
    }
