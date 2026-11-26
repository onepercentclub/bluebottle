"""
Clean up organizations:

1. Remove organizations that are not used by anything (activities, initiatives,
   linked activities, GoodUp Connect, members, payout accounts, ...).
2. Merge organizations that have the same name (case insensitive) into the oldest one.

Dry-run by default, add `fix` to actually change things.

  ./manage.py runscript cleanup_organizations
  ./manage.py runscript cleanup_organizations --script-args=fix
  ./manage.py runscript cleanup_organizations --script-args fix tenant=pggm
"""
from django.db import transaction

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.organizations.models import Organization
from scripts.cleanup_geolocations import suppress_elasticsearch_signals

COPY_FIELDS = ('website', 'logo', 'image', 'color')


def split_args(args):
    return [part for arg in args for part in str(arg).split()]


def get_clients(args):
    tenant = next((arg.split('=', 1)[1] for arg in args if arg.startswith('tenant=')), None)
    if tenant:
        return Client.objects.filter(schema_name=tenant)
    return Client.objects.exclude(schema_name='public')


def get_relations():
    """
    All relations pointing at an organization, except the translations
    that belong to the organization itself.
    """
    return [
        relation for relation in Organization._meta.related_objects
        if relation.get_accessor_name() != 'translations'
    ]


def is_used(organization, ignore_origin=False):
    if organization.origin_id and not ignore_origin:
        return True
    for relation in get_relations():
        if relation.related_model._base_manager.filter(
            **{relation.field.name: organization}
        ).exists():
            return True
    return False


def has_actor(organization):
    """
    Organizations that are the organization of a GoodUp Connect actor. An organization
    can only have one actor, so a group with more than one of these is not merged. The
    actor of a single one is moved to the organization we merge into. The `origin` link
    (the remote organization an organization was created from) is just a back reference
    and can be dropped.
    """
    return hasattr(organization, 'activity_pub_organization')


def remove_unused(fix=False):
    used = set(
        Organization.objects.exclude(origin__isnull=True).values_list('pk', flat=True)
    )
    for relation in get_relations():
        field = relation.field.name
        used.update(
            relation.related_model._base_manager
            .exclude(**{'{}__isnull'.format(field): True})
            .values_list(field, flat=True)
            .distinct()
        )

    unused = list(Organization.objects.exclude(pk__in=used).order_by('name'))
    removed_ids = set()
    for organization in unused:
        print('  remove unused: {} (id {})'.format(organization.name, organization.pk))
        removed_ids.add(organization.pk)
        if fix:
            organization.delete()
    return removed_ids


def merge_organizations(sources, target, fix=False):
    if not fix:
        return

    for relation in get_relations():
        if relation.one_to_one:
            continue
        relation.related_model._base_manager.filter(
            **{'{}__in'.format(relation.field.name): sources}
        ).update(**{relation.field.name: target})

    if not has_actor(target):
        for source in sources:
            if has_actor(source):
                actor = source.activity_pub_organization
                actor.organization = target
                actor.save(update_fields=['organization'])
                break

    changed = []
    if not target.origin_id:
        for source in sources:
            if source.origin_id:
                target.origin_id = source.origin_id
                changed.append('origin')
                break
    for field in COPY_FIELDS:
        if not getattr(target, field):
            for source in sources:
                if getattr(source, field):
                    setattr(target, field, getattr(source, field))
                    changed.append(field)
                    break
    if not target.verified and any(source.verified for source in sources):
        target.verified = True
        changed.append('verified')
    if changed:
        target.save(update_fields=changed)

    for source in sources:
        if is_used(source, ignore_origin=True):
            print('  ! {} (id {}) is still in use, not deleting'.format(source.name, source.pk))
            continue
        source.delete()


def merge_duplicates(skip_ids=(), fix=False):
    groups = {}
    for organization in Organization.objects.exclude(pk__in=skip_ids).order_by('pk'):
        groups.setdefault(organization.name.strip().lower(), []).append(organization)

    merged = 0
    skipped = 0
    for organizations in groups.values():
        if len(organizations) < 2:
            continue

        if sum(has_actor(organization) for organization in organizations) > 1:
            print('  skip merge, multiple GoodUp Connect actors: {} ({})'.format(
                organizations[0].name,
                ', '.join(str(organization.pk) for organization in organizations)
            ))
            skipped += 1
            continue

        target, *sources = organizations
        print('  merge {} into "{}" (id {})'.format(
            ', '.join('"{}" (id {})'.format(source.name, source.pk) for source in sources),
            target.name,
            target.pk,
        ))
        merge_organizations(sources, target, fix=fix)
        merged += len(sources)

    return merged, skipped


def cleanup_tenant(fix=False):
    removed_ids = remove_unused(fix=fix)
    merged, skipped = merge_duplicates(skip_ids=removed_ids, fix=fix)
    return len(removed_ids), merged, skipped


def run(*args):
    args = split_args(args)
    fix = 'fix' in args

    for client in get_clients(args):
        with LocalTenant(client):
            if SitePlatformSettings.load().terminated:
                continue

            print('##### Tenant: {} ({} organizations)'.format(client.name, Organization.objects.count()))

            if fix:
                with suppress_elasticsearch_signals():
                    with transaction.atomic():
                        removed, merged, skipped = cleanup_tenant(fix=True)
            else:
                removed, merged, skipped = cleanup_tenant(fix=False)

            print('{}: {} removed, {} merged, {} skipped{}'.format(
                client.name,
                removed,
                merged,
                skipped,
                '' if fix else ' (not saved)'
            ))

    if not fix:
        print("☝️ Add '--script-args=fix' to the command to actually clean up the organizations.")
