import subprocess
from multiprocessing.pool import Pool

from django.core.management import BaseCommand
from django.db import connection

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.sharing.consumers import consume_participants, consume_activities


def start_consumers(schema_name):
    print(f"Starting consumers for tenant {schema_name}")
    try:
        # Set up the tenant
        tenant = Client.objects.get(schema_name=schema_name)

        with LocalTenant(tenant):
            consume_activities()
            consume_participants()
    except Client.DoesNotExist:
        print(f"Tenant with schema_name '{schema_name}' does not exist.")
        return schema_name, 1  # Indicate failure
    except Exception as e:
        print(f"Unexpected error for tenant '{schema_name}': {e}")
        return schema_name, 1  # Indicate failure
    finally:
        # Close the database connection explicitly to clean up
        connection.close()
    return schema_name, 0


def run_for_tenant(schema_name):
    try:
        result = subprocess.run(
            ['./manage.py', 'start_consumers', '-s', schema_name],
        )
        if result.returncode != 0:
            print(f"Error for tenant {schema_name}: {result.stderr}")
            return schema_name, 1
        print(f"Started tenant {schema_name}")
        return schema_name, 0
    except Exception as e:
        print(f"Exception for tenant {schema_name}: {e}")
        return schema_name, 1


class Command(BaseCommand):
    help = 'Start consumers for all tenants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--processes',
            type=int,
            default=8,
            help='How many processes to run in parallel'
        )
        parser.add_argument(
            '-s',
            '--schema',
            type=str,
            default=None,
            help='Only run for the specified tenant schema'
        )

    def handle(self, *args, **options):
        tenant_schema = options['schema']
        if tenant_schema:
            schema, status = start_consumers(tenant_schema)
            if status != 0:
                print(f"Failed to start consumers for tenant {schema}")
        else:
            schemas = ['nlcares', 'dll', 'mars', 'onepercent', 'voor_je_buurt']

            pool = Pool(processes=options['processes'])
            tasks = [pool.apply_async(run_for_tenant, args=(schema_name,)) for schema_name in schemas]
            results = [task.get() for task in tasks]

            for tenant, result in results:
                if result != 0:
                    print(f'Tenant failed to start consumers: {tenant}')
            pool.close()
