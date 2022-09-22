from optparse import make_option

import subprocess
from multiprocessing import Pool
from bluebottle.common.management.commands.base import Command as BaseCommand

from bluebottle.clients.models import Client


def reindex(schema_name):
    print(f'reindexing tenant {schema_name}')
    return (
        schema_name,
        subprocess.call(
            f'./manage.py tenant_command  -s {schema_name} search_index --rebuild -f',
            shell=True
        )
    )


class Command(BaseCommand):
    help = 'Reindex all tenants'

    option_list = BaseCommand.options + (
        make_option(
            '--processes',
            default=8,
            help='How many processes run in parallel'
        ),
    )

    def handle(self, *args, **options):
        pool = Pool(processes=options['processes'])

        tasks = [pool.apply_async(reindex, args=[str(tenant.schema_name)]) for tenant in Client.objects.all()]

        results = [result.get() for result in tasks]

        for tenant, result in results:
            if result != 0:
                print(f'Tenant failed to index: {tenant}')

        pool.close()
