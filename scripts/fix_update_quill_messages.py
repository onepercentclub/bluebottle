import json

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.updates.models import Update


def is_quill_json(value):
    if value is None:
        return True
    if not isinstance(value, str) or value == '':
        return False
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return False
    return isinstance(parsed, dict) and 'html' in parsed


def to_quill_json(value):
    return json.dumps({'html': value or '', 'delta': ''})


def get_clients(args):
    tenant = next((arg.split('=', 1)[1] for arg in args if arg.startswith('tenant=')), None)
    if tenant:
        return Client.objects.filter(schema_name=tenant)
    return Client.objects.exclude(schema_name='public')


def fix_tenant(schema_name, dry_run=True):
    to_fix = []
    for pk, message in Update.objects.values_list('pk', 'message').iterator(chunk_size=500):
        if not is_quill_json(message):
            to_fix.append((pk, message))

    if not to_fix:
        print(f'{schema_name}: nothing to fix')
        return 0

    print(f'{schema_name}: {len(to_fix)} message(s) to fix')
    if dry_run:
        for pk, message in to_fix[:10]:
            preview = (message or '')[:80].replace('\n', ' ')
            print(f'  id={pk}: {preview!r}')
        if len(to_fix) > 10:
            print(f'  ... and {len(to_fix) - 10} more')
        return len(to_fix)

    for pk, message in to_fix:
        Update.objects.filter(pk=pk).update(message=to_quill_json(message))

    return len(to_fix)


def run(*args):
    fix = 'fix' in args
    clients = list(get_clients(args))
    if not clients:
        print('No matching tenants found.')
        return

    total = 0
    for client in clients:
        with LocalTenant(client, clear_tenant=True):
            total += fix_tenant(client.schema_name, dry_run=not fix)

    action = 'Would update' if not fix else 'Updated'
    print(f'{action} {total} update message(s) total')
    if total and not fix:
        print("☝️ Add '--script-args=fix' to actually write Quill JSON.")
