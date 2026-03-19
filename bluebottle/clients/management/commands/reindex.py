import subprocess
from multiprocessing import Pool
from optparse import make_option

from bluebottle.clients.models import Client
from bluebottle.common.management.commands.base import Command as BaseCommand


def reindex(schema_name, rebuild=False):
    """Reindex a tenant. If rebuild=False, use --populate to update in place."""
    print(f'reindexing tenant {schema_name}' + (' (rebuild)' if rebuild else ' (populate)'))
    if rebuild:
        cmd = f'./manage.py tenant_command -s {schema_name} search_index --rebuild -f'
    else:
        cmd = f'./manage.py tenant_command -s {schema_name} search_index --populate --refresh'
    return (schema_name, subprocess.call(cmd, shell=True))


class Command(BaseCommand):
    help = (
        'Reindex all tenants. By default uses --populate (update in place without '
        'dropping the index). Use --rebuild to recreate indices from scratch.'
    )

    option_list = BaseCommand.options + (
        make_option(
            '--processes',
            default=8,
            help='How many processes run in parallel'
        ),
        make_option(
            '-s',
            default=None,
            help='Only run for specified tenant schema'
        ),
        make_option(
            '--rebuild',
            action='store_true',
            default=False,
            help='Drop and recreate indices (full rebuild). Default is populate-only.'
        ),
    )

    def handle(self, *args, **options):
        tenant_schema = options['s']
        rebuild = options['rebuild']
        if tenant_schema:
            tenant, result = reindex(str(tenant_schema), rebuild=rebuild)
            if result != 0:
                print(f'Tenant failed to index: {tenant}')
        else:
            pool = Pool(processes=options['processes'])
            tasks = [
                pool.apply_async(reindex, args=[str(tenant.schema_name)], kwds={'rebuild': rebuild})
                for tenant in Client.objects.all()
            ]
            results = [result.get() for result in tasks]
            for tenant, result in results:
                if result != 0:
                    print(f'Tenant failed to index: {tenant}')
            pool.close()
