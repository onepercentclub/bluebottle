import argparse
import logging
import re
import time

import requests
from django.db.models import Q
from django.utils.translation import get_language

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.geo import mapbox as mapbox_utils
from bluebottle.geo.models import Geolocation

logger = logging.getLogger(__name__)

HOUSE_NUMBER_LEADING_PATTERN = re.compile(r'^(\d+[a-zA-Z\-/]*)')
HOUSE_NUMBER_BEFORE_COMMA_PATTERN = re.compile(r'\b(\d+[a-zA-Z\-/]*)\s*,')


def _housenumber_from_text(value):
    text = (value or '').strip()
    if not text:
        return None

    match = HOUSE_NUMBER_LEADING_PATTERN.search(text)
    if match:
        return match.group(1)

    match = HOUSE_NUMBER_BEFORE_COMMA_PATTERN.search(text)
    if match:
        return match.group(1)

    return None


def extract_housenumber(geolocation):
    if geolocation.street_number:
        return geolocation.street_number

    housenumber = _housenumber_from_text(geolocation.formatted_address)
    if housenumber:
        return housenumber

    return _housenumber_from_text(geolocation.street)


def _normalize_reverse_type(types):
    if not types:
        return None
    if isinstance(types, (list, tuple)):
        if len(types) == 1:
            return types[0]
        return None
    return types


def reverse_v6(longitude, latitude, types=None, language=None, limit=None):
    params = {
        'longitude': longitude,
        'latitude': latitude,
    }
    if language:
        params['language'] = language

    type_value = _normalize_reverse_type(types)
    if type_value:
        params['types'] = type_value
        if limit is not None:
            params['limit'] = limit

    return mapbox_utils._request('/reverse', params)


def forward_v6(
    query=None,
    address_number=None,
    street=None,
    postcode=None,
    place=None,
    region=None,
    country=None,
    types=None,
    language=None,
    limit=1,
):
    params = {'limit': limit}
    if language:
        params['language'] = language
    if types:
        params['types'] = ','.join(types) if isinstance(types, (list, tuple)) else types
    if query:
        params['q'] = query
    if address_number:
        params['address_number'] = address_number
    if street:
        params['street'] = street
    if postcode:
        params['postcode'] = postcode
    if place:
        params['place'] = place
    if region:
        params['region'] = region
    if country:
        params['country'] = country

    return mapbox_utils._request('/forward', params)


def _prefer_address_feature(response):
    features = response.get('features', [])
    for feature in features:
        properties = feature.get('properties', {})
        if properties.get('feature_type') == 'address':
            return feature
    return features[0] if features else None


def reverse_geocode_feature(longitude, latitude, language=None):
    languages = mapbox_utils.platform_language_param(language)
    try:
        response = reverse_v6(
            longitude,
            latitude,
            types='address',
            language=languages,
            limit=1,
        )
        feature = _prefer_address_feature(response)
        if feature:
            return feature
    except requests.RequestException as error:
        logger.warning('Mapbox reverse geocode (address) failed: %s', error)

    try:
        response = reverse_v6(longitude, latitude, language=languages)
        return _prefer_address_feature(response)
    except requests.RequestException as error:
        logger.warning('Mapbox reverse geocode failed: %s', error)
        return None


def parse_feature(feature):
    if not feature:
        return {}

    properties = feature.get('properties', {})
    context = properties.get('context', {})
    if not isinstance(context, dict):
        context = {}

    address_context = context.get('address', {})
    country_context = context.get('country', {})

    country_code = country_context.get('country_code', '')
    if country_code:
        country_code = country_code.upper()

    return {
        'mapbox_id': properties.get('mapbox_id'),
        'formatted_address': mapbox_utils.geofeature_place_name(
            properties.get('feature_type', ''),
            properties.get('name_preferred') or properties.get('name', ''),
            context,
            full_address=properties.get('full_address'),
        ),
        'street': address_context.get('street_name') or properties.get('name', ''),
        'street_number': address_context.get('address_number', ''),
        'postal_code': context.get('postcode', {}).get('name', ''),
        'locality': (
            context.get('place', {}).get('name')
            or context.get('locality', {}).get('name')
            or ''
        ),
        'province': context.get('region', {}).get('name', ''),
        'country_code': country_code,
    }


def apply_parsed_feature(geolocation, parsed):
    if not parsed:
        return

    if parsed.get('mapbox_id'):
        geolocation.mapbox_id = parsed['mapbox_id']
    if parsed.get('formatted_address'):
        geolocation.formatted_address = parsed['formatted_address'][:255]
    if parsed.get('street'):
        geolocation.street = parsed['street'][:255]
    if parsed.get('street_number'):
        geolocation.street_number = parsed['street_number'][:255]
    if parsed.get('postal_code'):
        geolocation.postal_code = parsed['postal_code'][:255]
    if parsed.get('locality'):
        geolocation.locality = parsed['locality'][:255]
    if parsed.get('province'):
        geolocation.province = parsed['province'][:255]

    country_code = parsed.get('country_code')
    if country_code:
        from bluebottle.geo.models import Country
        country = Country.objects.filter(alpha2_code=country_code).first()
        if country:
            geolocation.country = country


def resolve_geolocation_feature(geolocation, language=None):
    """Resolve a Mapbox v6 feature for legacy v5 / incomplete geolocations."""
    language = language or get_language() or 'en'

    if geolocation.mapbox_id and mapbox_utils.is_v6_mapbox_id(geolocation.mapbox_id):
        response = mapbox_utils.lookup_by_mapbox_id(geolocation.mapbox_id, language=language)
        return mapbox_utils._first_feature(response)

    if geolocation.mapbox_id and geolocation.mapbox_id.startswith('address.'):
        address_number = extract_housenumber(geolocation)
        country_code = None
        if geolocation.country_id and geolocation.country:
            country_code = geolocation.country.alpha2_code

        params = {
            'street': geolocation.street,
            'postcode': geolocation.postal_code,
            'place': geolocation.locality,
            'region': geolocation.province,
            'country': country_code,
            'types': ['address'],
            'language': mapbox_utils.platform_language_param(language),
        }
        if address_number:
            params['address_number'] = address_number
            response = forward_v6(**params)
            feature = _prefer_address_feature(response)
            if feature:
                return feature

        if geolocation.formatted_address:
            response = forward_v6(
                query=geolocation.formatted_address,
                types=['address'],
                language=mapbox_utils.platform_language_param(language),
            )
            feature = _prefer_address_feature(response)
            if feature:
                return feature

    if geolocation.mapbox_id:
        response = mapbox_utils.lookup_by_mapbox_id(geolocation.mapbox_id, language=language)
        feature = mapbox_utils._first_feature(response)
        if feature:
            return feature

    if geolocation.position:
        return reverse_geocode_feature(
            geolocation.position.x,
            geolocation.position.y,
            language=language,
        )

    if geolocation.formatted_address:
        response = forward_v6(
            query=geolocation.formatted_address,
            types=['address'],
            language=mapbox_utils.platform_language_param(language),
        )
        return _prefer_address_feature(response)

    return None


def migrate_geolocation(geolocation, dry_run=False):
    if mapbox_utils.is_v6_mapbox_id(geolocation.mapbox_id):
        if geolocation.geofeature_id:
            return 'skipped', 'already v6'
        return backfill_primary_geofeature(geolocation, dry_run=dry_run)

    feature = resolve_geolocation_feature(geolocation)
    if not feature:
        return 'failed', 'no feature found'

    parsed = parse_feature(feature)
    if not parsed.get('mapbox_id'):
        return 'failed', 'feature has no mapbox_id'

    if dry_run:
        return 'dry-run', parsed['mapbox_id']

    apply_parsed_feature(geolocation, parsed)
    geolocation.save(mapbox_feature=feature)
    geolocation.refresh_from_db()
    if not geolocation.geofeature_id:
        return 'failed', 'primary geofeature not set'
    return 'updated', parsed['mapbox_id']


def backfill_primary_geofeature(geolocation, dry_run=False):
    primary = mapbox_utils.select_primary_geofeature(geolocation)
    if primary:
        if dry_run:
            return 'dry-run', 'primary geofeature {}'.format(primary.mapbox_id)
        Geolocation.objects.filter(pk=geolocation.pk).update(geofeature=primary)
        return 'updated', 'primary geofeature {}'.format(primary.mapbox_id)

    feature = resolve_geolocation_feature(geolocation)
    if not feature:
        return 'failed', 'no feature found'

    if dry_run:
        return 'dry-run', 'sync geofeatures'

    mapbox_utils.sync_geofeatures(geolocation, feature)
    geolocation.refresh_from_db()
    if not geolocation.geofeature_id:
        return 'failed', 'primary geofeature not set'
    return 'updated', 'synced geofeatures'


def _normalize_script_args(args):
    args = list(args)
    if 'dry-run' in args:
        args = ['--dry-run'] + [value for value in args if value != 'dry-run']
    if '--tenant' in args:
        return args
    if args and not args[0].startswith('-'):
        return ['--tenant', args[0]] + args[1:]
    if len(args) >= 2 and not args[-1].startswith('-'):
        try:
            float(args[-1])
        except ValueError:
            if args[-2] != '--sleep':
                args = args[:-1] + ['--tenant', args[-1]]
    return args


def run(*args):
    parser = argparse.ArgumentParser(
        description='Migrate Geolocation mapbox_id from v5 to v6',
        epilog=(
            'Examples:\n'
            '  ./manage.py runscript migrate_mapbox --script-args pggm\n'
            '  ./manage.py runscript migrate_mapbox --script-args dry-run pggm'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--dry-run', action='store_true', help='Do not save changes')
    parser.add_argument('--tenant', help='Only migrate a single tenant schema name')
    parser.add_argument('--sleep', type=float, default=0.2, help='Delay between API calls')
    options = parser.parse_args(_normalize_script_args(args))

    tenants = Client.objects.exclude(domain_url__endswith='.p.goodup.com')
    if options.tenant:
        tenants = tenants.filter(schema_name=options.tenant)

    tenant_list = list(tenants)
    if not tenant_list:
        print('No tenants found{}'.format(
            ' for schema {!r}'.format(options.tenant) if options.tenant else ''
        ))
        return

    print(
        'Migrating mapbox ids for {} tenant(s){}'.format(
            len(tenant_list),
            ' (dry-run)' if options.dry_run else '',
        ),
        flush=True,
    )

    for tenant in tenant_list:
        with LocalTenant(tenant):
            locations = Geolocation.objects.exclude(
                Q(mapbox_id__isnull=True) |
                Q(mapbox_id='') |
                Q(mapbox_id='unknown')
            ).filter(
                Q(geofeature__isnull=True) |
                ~Q(mapbox_id__startswith='dXJu')
            )

            total = locations.count()
            print('{}: {} locations to migrate'.format(tenant.name, total), flush=True)

            updated = 0
            failed = 0
            skipped = 0

            for index, geolocation in enumerate(locations.iterator(), start=1):
                try:
                    status, detail = migrate_geolocation(
                        geolocation, dry_run=options.dry_run
                    )
                except Exception as error:
                    status = 'error'
                    detail = str(error)
                    failed += 1
                else:
                    if status == 'updated':
                        updated += 1
                    elif status == 'skipped':
                        skipped += 1
                    elif status in ('failed', 'error'):
                        failed += 1

                print(
                    '{} / {} [{}] {} - {}'.format(
                        index, total, status, geolocation.id, detail
                    ),
                    flush=True,
                )
                time.sleep(options.sleep)

            print(
                '{} done: {} updated, {} skipped, {} failed'.format(
                    tenant.name, updated, skipped, failed
                ),
                flush=True,
            )
