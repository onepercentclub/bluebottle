"""
Per-tenant geolocation maintenance: normalize mapbox ids, collect GeoFeatures, merge duplicates.

Usage:
    ./manage.py runscript get_geofeatures --script-args tenant=onepercent
    ./manage.py runscript get_geofeatures --script-args tenant=onepercent mismatch_km=50
"""
from django.conf import settings

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.geo.geofeatures import sync_geolocation
from bluebottle.geo.maintenance import (
    backfill_street_number_for_legacy_address_mapbox_ids,
    clear_null_island_positions,
    delete_unreferenced_geolocations,
    merge_duplicate_geolocations,
    position_is_null_island,
    resolve_mapbox_mismatch,
)
from bluebottle.geo.models import Geolocation


def run(*args):
    if not settings.MAPBOX_API_KEY:
        raise RuntimeError('settings.MAPBOX_API_KEY is not set')

    schema_name = None
    mapbox_mismatch_km = 50.0
    for arg in args:
        if arg.startswith('tenant='):
            schema_name = arg.split('=', 1)[1].strip() or None
        elif arg.startswith('mismatch_km='):
            mapbox_mismatch_km = float(arg.split('=', 1)[1])

    tenants = Client.objects.all()
    if schema_name:
        tenants = tenants.filter(schema_name=schema_name)

    tenant_list = list(tenants)
    if schema_name and not tenant_list:
        known = list(Client.objects.values_list('schema_name', flat=True).order_by('schema_name'))
        hint = ''
        if 'onepercent' in known and schema_name in ('onpercent', 'onepercentclub'):
            hint = ' Did you mean tenant=onepercent?'
        raise RuntimeError(
            f'No tenant with schema_name={schema_name!r}.{hint} '
            f'Known tenants: {", ".join(known) or "(none)"}'
        )

    if not tenant_list:
        print('No tenants to process.')
        return

    print(f'Processing {len(tenant_list)} tenant(s): {", ".join(t.schema_name for t in tenant_list)}')

    for tenant in tenant_list:
        with LocalTenant(tenant):
            print(f'{tenant.schema_name}: backfill street_number (address.*)…')
            n_backfill = backfill_street_number_for_legacy_address_mapbox_ids()
            print(f'{tenant.schema_name}: updated street_number on {n_backfill} rows')

            print(f'{tenant.schema_name}: delete geolocations with no reverse FK…')
            n_deleted = delete_unreferenced_geolocations()
            print(f'{tenant.schema_name}: deleted {n_deleted} unreferenced rows')

            print(f'{tenant.schema_name}: clear (0, 0) positions…')
            n_cleared = clear_null_island_positions()
            print(f'{tenant.schema_name}: cleared position on {n_cleared} rows')

            print(f'{tenant.schema_name}: merge duplicate geolocations…')
            n_merged = merge_duplicate_geolocations()
            print(f'{tenant.schema_name}: merged {n_merged} duplicate source rows')

            qs = Geolocation.objects.exclude(mapbox_id__startswith='dXJ').order_by('pk')
            total = qs.count()
            print(
                f'{tenant.schema_name}: sync {total} geolocations… '
                f'(mismatch_km={mapbox_mismatch_km})'
            )

            coords_cache = {}
            for n, location in enumerate(qs.iterator(), start=1):
                if position_is_null_island(location.position):
                    location.position = None

                try:
                    mismatch = resolve_mapbox_mismatch(
                        location,
                        max_dist_km=mapbox_mismatch_km,
                        coords_cache=coords_cache,
                    )
                except Exception:
                    mismatch = None

                if mismatch:
                    method, new_id, dist_km = mismatch
                    old = location.mapbox_id
                    location.mapbox_id = new_id
                    location.save()
                    print(
                        f'{tenant.schema_name}: pk={location.pk} mapbox mismatch '
                        f'{dist_km:.3f}km {method} old={old!r} new={location.mapbox_id!r}'
                    )
                    continue

                sync_geolocation(location)
                if n % 100 == 0 or n == total:
                    print(f'{tenant.schema_name}: sync {n}/{total}')

            n_merged = merge_duplicate_geolocations()
            print(f'{tenant.schema_name}: merged another {n_merged} duplicate source rows')
            print(f'{tenant.schema_name}: done')
