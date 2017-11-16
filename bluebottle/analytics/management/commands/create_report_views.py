import re

from django.core.management.base import BaseCommand
from django.conf import settings
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

        # Basic sanity check
        if not (re.match('^\s*DROP VIEW.*', report_sql.splitlines()[0]) and
                re.match('^\s*CREATE OR REPLACE VIEW.*', report_sql.splitlines()[1])):
            raise Exception('Is this a valid query to create a database view?')

        if options['tenant']:
            clients = [Client.objects.get(client_name=options['tenant'])]
        else:
            clients = Client.objects.all()

        for client in clients:
            connection.set_tenant(client)
            with LocalTenant(client, clear_tenant=True):
                cursor = connection.cursor()
                cursor.execute(report_sql)
