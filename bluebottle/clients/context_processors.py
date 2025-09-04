from bluebottle.utils.utils import get_client_ip

from bluebottle.cms.models import SitePlatformSettings
from django.db import connection
from bluebottle.clients import properties
from bluebottle.looker.models import LookerEmbed


def tenant(request):

    site_settings = SitePlatformSettings.load()

    context = {
        'tenant': connection.tenant,
        'properties': properties,
        'logo': site_settings.logo,
    }
    if hasattr(request, 'user') and request.user.has_perm('looker.access_looker_embeds'):
        context['looker_items'] = LookerEmbed.objects.all()

    context['client_ip'] = get_client_ip(request)

    return context
