import argparse
import time

from django.db.models import Q

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.geo import mapbox as mapbox_utils
from bluebottle.geo.models import Geolocation


def migrate_geolocation(geolocation, dry_run=False):
    if mapbox_utils.is_v6_mapbox_id(geolocation.mapbox_id):
        return 'skipped', 'already v6'

    feature = mapbox_utils.resolve_geolocation_feature(geolocation)
    if not feature:
        return 'failed', 'no feature found'

    parsed = mapbox_utils.parse_feature(feature)
    if not parsed.get('mapbox_id'):
        return 'failed', 'feature has no mapbox_id'

    if dry_run:
        return 'dry-run', parsed['mapbox_id']

    geolocation.save(
        skip_mapbox_sync=False,
        mapbox_feature=feature,
    )
    return 'updated', parsed['mapbox_id']


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
            '  ./manage.py runscript migrate_mapbox_v5_to_v6 --script-args pggm\n'
            '  ./manage.py runscript migrate_mapbox_v5_to_v6 --script-args dry-run pggm'
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
            ).exclude(
                mapbox_id__startswith='dXJu'
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
