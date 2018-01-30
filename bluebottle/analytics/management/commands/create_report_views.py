import re

from django.core.management.base import BaseCommand
from django.db import connection

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant


class Command(BaseCommand):
    help = 'Create report views (database)'

    def add_arguments(self, parser):
        parser.add_argument('--file', '-f', action='store', dest='file',
                            help="File path to sql for creating report views")
        parser.add_argument('--tenant', '-t', action='store', dest='tenant',
                            help="Tenant name")

    def handle(self, *args, **options):
        if options['file']:
            with open(options['file'], 'r') as file:
                report_sql = file.read()
        else:
            raise Exception('`Please specify either an sql file path')

        # Remove comments and blank lines
        sql_lines = filter(lambda x: not re.match(r'^(---.*|\s*)$', x), report_sql.splitlines())

        # Basic sanity check
        if not (re.match(r'^\s*DROP VIEW.*', sql_lines[0]) and
                re.match(r'^\s*CREATE OR REPLACE VIEW.*', sql_lines[1])):
            raise Exception('Is this a valid query to create a database view?')

        if options['tenant']:
            clients = [Client.objects.get(client_name=options['tenant'])]
        else:
            clients = Client.objects.all()

        sql = "\n".join(sql_lines)

        for client in clients:
            with LocalTenant(client, clear_tenant=True):
                cursor = connection.cursor()
                cursor.execute(sql)
