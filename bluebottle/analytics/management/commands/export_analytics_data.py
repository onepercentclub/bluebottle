import argparse
from datetime import datetime
import logging

import django.apps
from django.core.management.base import BaseCommand
from django.db import connection
from django.test.utils import override_settings
from django.utils import dateparse

from bluebottle.analytics.utils import process
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant


logger = logging.getLogger('console')

class Command(BaseCommand):
    help = 'import database contents into influxdb & save them in influxdb json format'

    @staticmethod
    def _validate_date(date_string):
        try:
            datetime.strptime(date_string, '%Y-%m-%d')
            return date_string
        except ValueError:
            msg = '{} is not a valid date or is not in the required date format YYYY-MM-DD'.format(date_string)
            raise argparse.ArgumentTypeError(msg)

    def add_arguments(self, parser):
        #TODO: Add arguments to select export destination
        #TODO: Add arguments to select specific tenant
        parser.add_argument('--start', metavar='YYYY-MM-DD', action='store', dest='start', required=True,
                            type=self._validate_date,
                            help="Start date (YYYY-MM-DD) for dump. UTC is the default time zone")

        parser.add_argument('--end',  metavar='YYYY-MM-DD', action='store', dest='end', required=True,
                            type=self._validate_date,
                            help="End date (YYYY-MM-DD) for dump. UTC is the default time zone")

    """ Dump analytics records for all tenants over a given date range """
    def handle(self, **options):
        start_date = dateparse.parse_datetime('{} 00:00:00+00:00'.format(options['start']))
        end_date = dateparse.parse_datetime('{} 23:59:59+00:00'.format(options['end']))

        for client in Client.objects.all():
            connection.set_tenant(client)

            with LocalTenant(client, clear_tenant=True):
                logger.info('tenant:{}'.format(client.schema_name))
                models = django.apps.apps.get_models()

                for model in models:
                    if hasattr(model, 'Analytics'):
                        self._process(model, start_date, end_date)

    @override_settings(ANALYTICS_ENABLED=True)
    def _process(self, cls, start_date, end_date):
        cls_name = cls.__name__
        if cls_name == 'Member':
            results = cls.objects.all().filter(date_joined__gte=start_date,
                                               date_joined__lte=end_date)
            for result in results:
                process(result, True, result.date_joined)
        elif cls_name in ['Project', 'Task', 'TaskMember', 'Wallpost', 'Reaction', 'Order', 'Vote']:
            results = cls.objects.all().filter(created__gte=start_date, created__lte=end_date)
            logger.info('record_type:{} records_written:{}'.format(cls_name, results.count()))
            for result in results:
                process(result, True, result.created)
