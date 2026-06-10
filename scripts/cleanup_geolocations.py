import argparse
from contextlib import contextmanager

from django.apps import apps
from django.db import transaction
from django.db.models import Count

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.geo.models import Geolocation


@contextmanager
def suppress_elasticsearch_signals():
    ded_config = apps.get_app_config('django_elasticsearch_dsl')
    processor = ded_config.signal_processor
    if processor:
        processor.teardown()
    try:
        yield
    finally:
        if processor:
            processor.setup()


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


def geolocation_is_used(geolocation):
    for relation in Geolocation._meta.related_objects:
        accessor_name = relation.get_accessor_name()
        if getattr(geolocation, accessor_name).exists():
            return True
    return False


def pick_canonical_geolocation(geolocations):
    geolocations = list(geolocations)
    used = [geolocation for geolocation in geolocations if geolocation_is_used(geolocation)]
    candidates = used or geolocations
    return min(candidates, key=lambda geolocation: geolocation.pk)


def repoint_geolocation_references(source, target, dry_run=False):
    repointed = 0
    for relation in Geolocation._meta.related_objects:
        accessor_name = relation.get_accessor_name()
        field_name = relation.field.name
        related_queryset = getattr(source, accessor_name)
        count = related_queryset.count()
        if not count:
            continue
        repointed += count
        if not dry_run:
            related_queryset.update(**{field_name: target})
    return repointed


def merge_geofeatures(source, target, dry_run=False):
    geofeature_ids = list(source.geofeatures.values_list('pk', flat=True))
    if not geofeature_ids:
        return 0
    if not dry_run:
        target.geofeatures.add(*geofeature_ids)
    return len(geofeature_ids)


def delete_geolocation(geolocation, dry_run=False):
    if dry_run:
        return
    Geolocation.objects.filter(pk=geolocation.pk).delete()


def merge_geolocation(source, target, dry_run=False):
    repointed = repoint_geolocation_references(source, target, dry_run=dry_run)
    geofeatures_merged = merge_geofeatures(source, target, dry_run=dry_run)
    if not dry_run:
        delete_geolocation(source, dry_run=False)
    return repointed, geofeatures_merged


def deduplicate_geolocations(dry_run=False):
    duplicate_groups = (
        Geolocation.objects
        .values('mapbox_id', 'formatted_address')
        .annotate(count=Count('id'))
        .filter(count__gt=1)
        .order_by('-count')
    )

    groups_processed = 0
    merged_count = 0
    repointed_count = 0
    geofeatures_merged = 0

    for group in duplicate_groups:
        geolocations = Geolocation.objects.filter(
            mapbox_id=group['mapbox_id'],
            formatted_address=group['formatted_address'],
        ).order_by('pk')
        canonical = pick_canonical_geolocation(geolocations)
        duplicates = geolocations.exclude(pk=canonical.pk)
        if not duplicates.exists():
            continue

        groups_processed += 1
        print(
            'Duplicate group mapbox_id={!r} formatted_address={!r} ({} records, keeping {})'.format(
                group['mapbox_id'],
                group['formatted_address'],
                group['count'],
                canonical.pk,
            ),
            flush=True,
        )

        for duplicate in duplicates:
            repointed, merged_features = merge_geolocation(
                duplicate, canonical, dry_run=dry_run
            )
            repointed_count += repointed
            geofeatures_merged += merged_features
            merged_count += 1
            print(
                '  merged {} -> {} ({} references repointed, {} geofeatures)'.format(
                    duplicate.pk,
                    canonical.pk,
                    repointed,
                    merged_features,
                ),
                flush=True,
            )

    return {
        'groups_processed': groups_processed,
        'merged_count': merged_count,
        'repointed_count': repointed_count,
        'geofeatures_merged': geofeatures_merged,
    }


def remove_unused_geolocations(dry_run=False):
    removed_count = 0
    unused_geolocations = [
        geolocation
        for geolocation in Geolocation.objects.order_by('pk').iterator()
        if not geolocation_is_used(geolocation)
    ]

    for geolocation in unused_geolocations:
        removed_count += 1
        print(
            'Removing unused geolocation {} ({!r})'.format(
                geolocation.pk,
                geolocation.formatted_address or geolocation.mapbox_id or '',
            ),
            flush=True,
        )
        delete_geolocation(geolocation, dry_run=dry_run)

    return {'removed_count': removed_count}


def cleanup_tenant(dry_run=False):
    dedupe_stats = deduplicate_geolocations(dry_run=dry_run)
    unused_stats = remove_unused_geolocations(dry_run=dry_run)
    return {**dedupe_stats, **unused_stats}


def run(*args):
    parser = argparse.ArgumentParser(
        description='Deduplicate and remove unused Geolocation records',
        epilog=(
            'Examples:\n'
            '  ./manage.py runscript cleanup_geolocations --script-args pggm\n'
            '  ./manage.py runscript cleanup_geolocations --script-args dry-run pggm'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--dry-run', action='store_true', help='Do not save changes')
    parser.add_argument('--tenant', help='Only clean up a single tenant schema name')
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
        'Cleaning up geolocations for {} tenant(s){}'.format(
            len(tenant_list),
            ' (dry-run)' if options.dry_run else '',
        ),
        flush=True,
    )

    for tenant in tenant_list:
        with LocalTenant(tenant):
            total_before = Geolocation.objects.count()
            print('{}: {} geolocations before cleanup'.format(tenant.name, total_before), flush=True)

            if options.dry_run:
                stats = cleanup_tenant(dry_run=True)
            else:
                with suppress_elasticsearch_signals():
                    with transaction.atomic():
                        stats = cleanup_tenant(dry_run=False)

            total_after = Geolocation.objects.count()
            print(
                '{} done: {} duplicate groups, {} merged, {} references repointed, '
                '{} unused removed ({} -> {} geolocations)'.format(
                    tenant.name,
                    stats['groups_processed'],
                    stats['merged_count'],
                    stats['repointed_count'],
                    stats['removed_count'],
                    total_before,
                    total_after,
                ),
                flush=True,
            )
