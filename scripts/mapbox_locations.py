from django.db.models import Q

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.geo.models import Geolocation


def run(*args):
    for tenant in Client.objects.exclude(domain_url__endswith='.p.goodup.com').all():
        with LocalTenant(tenant):
            locations = Geolocation.objects.filter(
                Q(mapbox_id='unknown') |
                Q(mapbox_id__isnull=True) |
                Q(mapbox_id='')
            ).all()
            total = locations.count()
            t = 0
            for location in locations:
                t += 1
                location.save()
                print(f"{t} / {total} {tenant.name}")
