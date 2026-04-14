from django.conf import settings

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.geo.models import Geolocation
from bluebottle.geo.utils import collect_geo_features


def run(*args):
    if not settings.MAPBOX_API_KEY:
        raise RuntimeError('settings.MAPBOX_API_KEY is not set')

    for tenant in Client.objects.all():
        with LocalTenant(tenant):
            locations = (
                Geolocation.objects.filter(position__isnull=False)
                .exclude(mapbox_id__isnull=True)
                .exclude(mapbox_id='')
            )

            total = locations.count()
            count = 0
            for location in locations.iterator():
                count += 1
                migrated = collect_geo_features(location)
                if count % 100 == 0:
                    print(f'{tenant.schema_name}: {count}/{total}')
                if migrated:
                    print(
                        f'{tenant.schema_name}: geolocation {location.pk}: '
                        f'migrated {migrated} features'
                    )

