# from datetime import timedelta
import django.apps
from django.db import connection
from django.core.management.commands.makemessages import Command as BaseCommand
# from django.utils import timezone as tz
from django.test.utils import override_settings
from django.utils import dateparse

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.analytics.utils import process


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--start', action='store', dest='start',
                            help="Start date (YYYY-MM-DD) for dump.")

        parser.add_argument('--end', action='store', dest='end',
                            help="End date (YYYY-MM-DD) for dump.")

    """ Dump analytics records over a given date range """
    def handle(self, **options):
        start_date = dateparse.parse_datetime('{} 00:00:00+00:00'.format(options['start']))
        end_date = dateparse.parse_datetime('{} 23:59:59+00:00'.format(options['end']))

        for client in Client.objects.all():
            connection.set_tenant(client)

            with LocalTenant(client, clear_tenant=True):
                print '\n\n{}'.format(client.schema_name)
                models = django.apps.apps.get_models()

                # import ipdb; ipdb.set_trace()
                for model in models:
                    if getattr(model, 'Analytics', None):

                        self._process(model, start_date, end_date)

    @override_settings(ANALYTICS_ENABLED=True)
    def _process(self, cls, start_date, end_date):
        # start_date = tz.datetime(year=2016, month=11, day=20,
        #                          tzinfo=timezone(settings.TIME_ZONE))
        # end_date = tz.datetime(year=2016, month=11, day=21,
        #                        tzinfo=timezone(settings.TIME_ZONE))

        # start_date = tz.datetime(year=2016, month=10, day=31,
        #                          tzinfo=timezone(settings.TIME_ZONE))
        # end_date = tz.datetime(year=2016, month=11, day=4,
        #                        tzinfo=timezone(settings.TIME_ZONE))

        # Skip projects / tasks / taskmembers for now
        results = []
        cls_name = cls.__name__
        if cls_name in ['Project', 'Task', 'TaskMember']:
            return
        elif cls_name == 'Member':
            results = cls.objects.all().filter(date_joined__gte=start_date,
                                               date_joined__lte=end_date)
            for result in results:
                process(result, True, result.date_joined)
        elif cls_name in ['Wallpost', 'Reaction', 'Order', 'Vote']:
            results = cls.objects.all().filter(created__gte=start_date, created__lte=end_date)
            print 'Dumping {} records for {}:'.format(results.count(), cls_name)
            for result in results:
                process(result, True, result.created)
                # try:
                #     process(result, result.date_joined)
                # except AttributeError as err:
                #     print 'Whatt!!!!: {}'.format(err.message)
