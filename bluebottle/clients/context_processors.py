from bluebottle.utils.utils import get_client_ip

from bluebottle.cms.models import SitePlatformSettings
from django.db import connection
from bluebottle.clients import properties
from bluebottle.looker.models import LookerEmbed

from django.conf import settings


def tenant(request):

    site_settings = SitePlatformSettings.load()

    context = {
        'tenant': connection.tenant,
        'properties': properties,
        'logo': site_settings.logo,
        'platform_name': site_settings.platform_name
        # Add color settings for admin templates
        'action_color': site_settings.action_color,
        'action_text_color': site_settings.action_text_color,
        'description_color': site_settings.description_color,
        'description_text_color': site_settings.description_text_color,
        'link_color': site_settings.link_color,
    }
    if hasattr(request, 'user') and request.user.has_perm('looker.access_looker_embeds'):
        context['looker_items'] = LookerEmbed.objects.all()

    context['client_ip'] = get_client_ip(request)
    context['VPN_CLIENT_IP'] = getattr(settings, 'VPN_CLIENT_IP', None)

    return context
