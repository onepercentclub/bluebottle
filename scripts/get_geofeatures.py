from collections import defaultdict

from django.conf import settings
from django.db import transaction
from django.db.models import Q

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.geo.models import Geolocation
from bluebottle.geo.utils import extract_house_number_from_address_fields


def backfill_street_number_for_legacy_address_mapbox_ids():
    qs = Geolocation.objects.filter(mapbox_id__startswith='address.').filter(
        Q(street_number__isnull=True) | Q(street_number=''),
    )
    batch = []
    batch_size = 500
    updated = 0
    for obj in qs.iterator():
        num = extract_house_number_from_address_fields(
            street_number=obj.street_number,
            street=obj.street,
            formatted_address=obj.formatted_address,
        )
        if not num:
            continue
        obj.street_number = num
        batch.append(obj)
        updated += 1
        if len(batch) >= batch_size:
            Geolocation.objects.bulk_update(batch, ['street_number'])
            batch = []
    if batch:
        Geolocation.objects.bulk_update(batch, ['street_number'])
    return updated


def delete_unreferenced_geolocations():
    referenced = set()
    for rel in Geolocation._meta.related_objects:
        if not rel.one_to_many:
            continue
        fk_name = rel.field.name
        rel_model = rel.related_model
        qs = rel_model.objects.exclude(**{f'{fk_name}__isnull': True}).values_list(
            fk_name, flat=True,
        )
        for pk in qs.iterator(chunk_size=5000):
            if pk is not None:
                referenced.add(pk)

    if referenced:
        orphan_qs = Geolocation.objects.exclude(pk__in=referenced)
    else:
        orphan_qs = Geolocation.objects.all()

    batch_size = 500
    deleted = 0
    while True:
        batch = list(
            orphan_qs.order_by('pk').values_list('pk', flat=True)[:batch_size],
        )
        if not batch:
            break
        deleted += len(batch)
        Geolocation.objects.filter(pk__in=batch).delete()
    return deleted


def _cluster_key(row):
    mapbox_id = (row.get('mapbox_id') or '').strip()
    if not mapbox_id:
        return None
    if mapbox_id.startswith('address.'):
        sn = row.get('street_number')
        sn_key = '' if sn is None else str(sn).strip()
        return ('address', mapbox_id, sn_key)
    return ('other', mapbox_id)


def merge_geolocations_fk_only(source, target):
    with transaction.atomic():
        for feature in source.features.all():
            target.features.add(feature)
        for rel in Geolocation._meta.related_objects:
            if rel.one_to_many:
                rel.related_model.objects.filter(**{
                    rel.field.name: source,
                }).update(**{
                    rel.field.name: target,
                })
        source.delete()


def merge_duplicate_geolocations():
    rows = (
        Geolocation.objects.exclude(
            Q(mapbox_id__isnull=True) | Q(mapbox_id=''),
        )
        .values('pk', 'mapbox_id', 'street_number')
        .order_by('pk')
    )

    groups = defaultdict(list)
    for row in rows.iterator(chunk_size=2000):
        key = _cluster_key(row)
        if key is None:
            continue
        groups[key].append(row['pk'])

    merged_sources = 0
    for _key, pks in groups.items():
        if len(pks) < 2:
            continue
        pks.sort()
        target_pk = pks[0]
        target = Geolocation.objects.get(pk=target_pk)
        for source_pk in pks[1:]:
            source = Geolocation.objects.get(pk=source_pk)
            merge_geolocations_fk_only(source, target)
            merged_sources += 1
    return merged_sources


def run(*args):
    if not settings.MAPBOX_API_KEY:
        raise RuntimeError('settings.MAPBOX_API_KEY is not set')

    for tenant in Client.objects.all():
        with LocalTenant(tenant):
            print(f'{tenant.schema_name}: backfill street_number (address.*)…')
            n_backfill = backfill_street_number_for_legacy_address_mapbox_ids()
            print(f'{tenant.schema_name}: updated street_number on {n_backfill} rows')

            print(f'{tenant.schema_name}: delete geolocations with no reverse FK…')
            n_deleted = delete_unreferenced_geolocations()
            print(f'{tenant.schema_name}: deleted {n_deleted} unreferenced rows')

            print(f'{tenant.schema_name}: merge duplicate geolocations…')
            n_merged = merge_duplicate_geolocations()
            print(f'{tenant.schema_name}: merged {n_merged} duplicate source rows')

            qs = Geolocation.objects.all().order_by('pk')
            total = qs.count()
            print(f'{tenant.schema_name}: save {total} geolocations (normalize + collect_geo_features)…')
            for n, location in enumerate(qs.iterator(), start=1):
                location.save()
                if n % 100 == 0 or n == total:
                    print(f'{tenant.schema_name}: save {n}/{total}')

            print(f'{tenant.schema_name}: done')
