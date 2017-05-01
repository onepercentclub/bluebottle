import argparse
import logging
from collections import defaultdict
from datetime import datetime, timedelta

import xlsxwriter
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count, Sum
from django.utils import dateparse
from django.conf import settings

from bluebottle.analytics.tasks import queue_analytics_record
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.members.models import Member
from bluebottle.orders.models import Order
from bluebottle.projects.models import Project

logger = logging.getLogger(__name__)


# TODO: Write the time frame (start_date and end_date) from the command line to the file
# TODO: Add charts
# NOTE: Score is a numeric value, Rating is a textual classification based on the score

class Command(BaseCommand):
    help = 'Export the engagement metrics'

    def __init__(self, **kwargs):
        super(Command, self).__init__(**kwargs)

        self.tenants = []

        for client in Client.objects.all():
            self.tenants.append(client.client_name)

        self.start_date = ''
        self.end_date = ''

        self.row_counter_engagement_raw_data = 1
        self.row_counter_engagement_aggregated_data = 1

        self.engagement_parameters = ['total_members', 'projects_done', 'projects_realised', 'donations_anonymous',
                                      'engagement_score_not_engaged', 'engagement_score_little_engaged',
                                      'engagement_score_very_engaged', 'engagement_score_engaged', 'total_engaged']

    def add_arguments(self, parser):

        # TODO: Add arguments to select export destination
        parser.add_argument('--start', metavar='YYYY-MM-DD', action='store', dest='start', required=True,
                            type=self._validate_date, help="Start date (YYYY-MM-DD) for dump. UTC is the default \
                            time zone")

        parser.add_argument('--end', metavar='YYYY-MM-DD', action='store', dest='end', required=True,
                            type=self._validate_date,
                            help="End date (YYYY-MM-DD) for dump. UTC is the default time zone")

        parser.add_argument('--tenants', metavar='TENANTS', action='store', dest='tenants', required=False, nargs='*',
                            choices=self.tenants, help="The names of the tenants to export")

        parser.add_argument('--export-to', action='store', dest='export_to', required=True, choices=['xls', 'influxdb'],
                            help="The export destination")

    @staticmethod
    def _validate_date(date_string):

        try:
            datetime.strptime(date_string, '%Y-%m-%d')
            return date_string
        except ValueError:
            msg = '{} is not a valid date or is not in the required date format YYYY-MM-DD'.format(date_string)
            raise argparse.ArgumentTypeError(msg)

    def handle(self, **options):
        self.tenants = set(options['tenants']) if options['tenants'] else None

        self.start_date = dateparse.parse_datetime('{} 00:00:00+00:00'.format(options['start']))
        self.end_date = dateparse.parse_datetime('{} 00:00:00+00:00'.format(options['end']))

        if options['export_to'] == 'xls':
            self.generate_engagement_xls()
        elif options['export_to'] == 'influxdb':
            end_date = self.end_date
            current_end_date = self.start_date + timedelta(days=1)
            while current_end_date <= end_date:
                self.end_date = current_end_date
                aggregated_engagement_data = self.store_engagement_tenant_data()
                self.store_engagement_aggregated_data(aggregated_engagement_data)

                # increment start date and end date by one day
                self.start_date = self.start_date + timedelta(days=1)
                current_end_date = current_end_date + timedelta(days=1)

    def generate_engagement_data(self):
        engagement_data = {}

        for client in Client.objects.all():
            if self.tenants is None or client.client_name in self.tenants:
                connection.set_tenant(client)
                with LocalTenant(client, clear_tenant=True):
                    logger.info('export tenant:{} start_date:{} end_date:{}'
                                .format(client.client_name,
                                        self.start_date.strftime('%Y-%m-%d %H:%M:%S'),
                                        self.end_date.strftime('%Y-%m-%d %H:%M:%S')))
                    client_raw_data = self.generate_raw_data()
                    client_aggregated_data = self.generate_aggregated_data(client_raw_data)
                    engagement_data[client.client_name] = client_aggregated_data

        return engagement_data

    def store_engagement_tenant_data(self):
        engagement_data = self.generate_engagement_data()
        aggregated_engagement_data = defaultdict(int)

        for client_name, data in engagement_data.iteritems():
            tags = {'type': 'engagement_number_tenant', 'tenant': client_name}
            fields = {'start_date': self.start_date.isoformat(),
                      'end_date': self.end_date.isoformat()
                      }
            for item in self.engagement_parameters:
                fields[item] = data[item]
                aggregated_engagement_data[item] += data[item]

            fields['engagement_number'] = data['total_engaged'] + data['donations_anonymous']

            if getattr(settings, 'CELERY_RESULT_BACKEND', None):
                queue_analytics_record.delay(timestamp=self.end_date, tags=tags, fields=fields)
            else:
                queue_analytics_record(timestamp=self.end_date, tags=tags, fields=fields)

        return aggregated_engagement_data

    def store_engagement_aggregated_data(self, aggregated_engagement_data):
        tags = {'type': 'engagement_number_aggregate'}

        fields = {'start_date': self.start_date.isoformat(),
                  'end_date': self.end_date.isoformat()
                  }

        for item in self.engagement_parameters:
            fields[item] = aggregated_engagement_data[item]

        fields['engagement_number'] = aggregated_engagement_data['total_engaged'] + \
            aggregated_engagement_data['donations_anonymous']

        if getattr(settings, 'CELERY_RESULT_BACKEND', None):
            queue_analytics_record.delay(timestamp=self.end_date, tags=tags, fields=fields)
        else:
            queue_analytics_record(timestamp=self.end_date, tags=tags, fields=fields)

    @staticmethod
    def get_engagement_score(entry):
        """
        Engaged member is someone who initiated project, wrote a comment, voted, made donation or did task
        Comment	            1 point
        Vote	            2 points
        Donation            4 points
        Task	            Each hour 1 point
        Fundraiser	        10 points
        Project Initiated	12 points
        """

        return entry['comments'] * 1 + entry['votes'] * 2 + entry['donations'] * 4 + \
            entry['tasks'] + entry['fundraisers'] * 10 + entry['projects'] * 12

    @staticmethod
    def get_engagement_rating(score):
        try:
            score = int(score)
            if score == 0:
                return 'not engaged'
            elif 0 < score <= 4:
                return 'little engaged'
            elif 4 < score <= 8:
                return 'engaged'
            elif score > 8:
                return 'very engaged'
        except (ValueError, TypeError):
            return 'invalid engagement score: {}'.format(score)

    @staticmethod
    def initialize_work_sheet(workbook, name, headers):
        worksheet = workbook.get_worksheet_by_name(name)
        if not worksheet:
            worksheet = workbook.add_worksheet(name)
            worksheet.write_row(0, 0, headers)
        return worksheet

    @staticmethod
    def get_xls_file_name(start_date, end_date):

        return 'engagement_report_{}_{}_generated_{}.xlsx'.format(start_date.strftime("%Y%m%d"),
                                                                  end_date.strftime("%Y%m%d"),
                                                                  datetime.now().strftime("%Y%m%d-%H%M%S"))

    def generate_engagement_xls(self):
        file_name = self.get_xls_file_name(self.start_date, self.end_date)

        with xlsxwriter.Workbook(file_name) as workbook:
            for client in Client.objects.all():
                if self.tenants is None or client.client_name in self.tenants:
                    connection.set_tenant(client)
                    with LocalTenant(client, clear_tenant=True):
                        logger.info('export tenant:{}'.format(client.client_name))
                        raw_data = self.generate_raw_data()
                        aggregated_data = self.generate_aggregated_data(raw_data)
                        self.generate_raw_data_worksheet(workbook, client.client_name, raw_data)
                        self.generate_aggregated_data_worksheet(workbook, client.client_name, aggregated_data)

    def generate_raw_data(self):
        raw_data = {}
        members = Member.objects.all()

        for member in members:
            raw_data[member.id] = defaultdict(int)
            raw_data[member.id]['year_last_seen'] = getattr(member.last_seen, 'year', '')

        raw_data = self.generate_comments_raw_data(raw_data)
        raw_data = self.generate_votes_raw_data(raw_data)
        raw_data = self.generate_donations_raw_data(raw_data)
        raw_data = self.generate_fundraisers_raw_data(raw_data)
        raw_data = self.generate_projects_raw_data(raw_data)
        raw_data = self.generate_tasks_raw_data(raw_data)
        raw_data = self.generate_raw_scores(raw_data)

        return raw_data

    def generate_raw_scores(self, data):
        for _, entry in data.iteritems():
            score = self.get_engagement_score(entry)
            entry['engagement_score'] = score
            entry['engagement_rating'] = self.get_engagement_rating(score)
        return data

    def generate_comments_raw_data(self, raw_data):
        members = Member.objects \
            .filter(wallpost_wallpost__created__gte=self.start_date,
                    wallpost_wallpost__created__lt=self.end_date) \
            .annotate(comments_total=Count('wallpost_wallpost')) \
            .values('id', 'comments_total')

        for member in members:
            raw_data[member['id']]['comments'] = member['comments_total']

        return raw_data

    def generate_votes_raw_data(self, raw_data):
        members = Member.objects \
            .filter(vote__created__gte=self.start_date, vote__created__lt=self.end_date) \
            .annotate(votes_total=Count('vote')) \
            .values('id', 'votes_total')

        for member in members:
            raw_data[member['id']]['votes'] = member['votes_total']

        return raw_data

    def generate_donations_raw_data(self, raw_data):
        members = Member.objects \
            .filter(order__created__gte=self.start_date, order__created__lt=self.end_date,
                    order__status="success", id__isnull=False) \
            .annotate(donations_total=Count('order')) \
            .values('id', 'donations_total')

        for member in members:
            raw_data[member['id']]['donations'] = member['donations_total']

        return raw_data

    def generate_fundraisers_raw_data(self, raw_data):
        members = Member.objects \
            .filter(fundraiser__created__gte=self.start_date, fundraiser__created__lt=self.end_date) \
            .annotate(fundraisers_total=Count('fundraiser')) \
            .values('id', 'fundraisers_total')

        for member in members:
            raw_data[member['id']]['fundraisers'] = member['fundraisers_total']

        return raw_data

    def generate_projects_raw_data(self, raw_data):
        members = Member.objects \
            .filter(owner__created__gte=self.start_date,
                    owner__created__lt=self.end_date,
                    owner__status__slug__in=['voting', 'voting-done', 'campaign',
                                             'to-be-continued', 'done-complete',
                                             'done-incomplete']) \
            .annotate(projects_total=Count('owner')) \
            .values('id', 'projects_total')

        for member in members:
            raw_data[member['id']]['projects'] = member['projects_total']

        return raw_data

    def generate_tasks_raw_data(self, raw_data):
        members = Member.objects \
            .filter(tasks_taskmember_related__created__gte=self.start_date,
                    tasks_taskmember_related__created__lt=self.end_date,
                    tasks_taskmember_related__status='realized',
                    tasks_taskmember_related__time_spent__gt=0) \
            .annotate(tasks_total=Sum('tasks_taskmember_related__time_spent')) \
            .values('id', 'tasks_total')

        for member in members:
            raw_data[member['id']]['tasks'] = member['tasks_total']

        return raw_data

    def generate_raw_data_worksheet(self, workbook, organisation, raw_data):
        worksheet_raw_data = self.initialize_raw_data_worksheet(workbook)
        self.write_raw_data(organisation, worksheet_raw_data, raw_data)
        return worksheet_raw_data

    def initialize_raw_data_worksheet(self, workbook):
        name = 'Engagement Raw Data'
        headers = ('organisation', 'member id', 'comments', 'votes', 'donations', 'fundraisers', 'projects', 'tasks',
                   'year_last_seen', 'engagement_score', 'engagement_rating')

        return self.initialize_work_sheet(workbook, name, headers)

    def write_raw_data(self, organisation, worksheet, data):

        for member_id, entry in data.iteritems():
            worksheet.write(self.row_counter_engagement_raw_data, 0, organisation)
            worksheet.write(self.row_counter_engagement_raw_data, 1, member_id)
            worksheet.write(self.row_counter_engagement_raw_data, 2, entry['comments'])
            worksheet.write(self.row_counter_engagement_raw_data, 3, entry['votes'])
            worksheet.write(self.row_counter_engagement_raw_data, 4, entry['donations'])
            worksheet.write(self.row_counter_engagement_raw_data, 5, entry['fundraisers'])
            worksheet.write(self.row_counter_engagement_raw_data, 6, entry['projects'])
            worksheet.write(self.row_counter_engagement_raw_data, 7, entry['tasks'])
            worksheet.write(self.row_counter_engagement_raw_data, 8, entry['year_last_seen'])
            worksheet.write(self.row_counter_engagement_raw_data, 9, entry['engagement_score'])
            worksheet.write(self.row_counter_engagement_raw_data, 10, entry['engagement_rating'])

            self.row_counter_engagement_raw_data += 1

    def generate_aggregated_data_worksheet(self, workbook, organisation, aggregated_data):
        worksheet_aggregated_data = self.initialize_aggregated_data_worksheet(workbook)
        self.write_aggregated_data(organisation, worksheet_aggregated_data, aggregated_data)

    def initialize_aggregated_data_worksheet(self, workbook):
        name = 'Engagement Aggregated Data'
        headers = ('organisation',
                   'total no. of platforms',
                   'total members',
                   'not engaged members (engagement score: 0)',
                   'little engaged members (engagement score: 1-3)',
                   'engaged members (engagement score: 4-8)',
                   'very engaged members (engagement score: >8)',
                   'total engaged members (engagement score: >4)',
                   '% total engaged members (engagement score: >4)',
                   'Projects Realised',
                   'Projects Done',
                   'Guest Donations'
                   )

        return self.initialize_work_sheet(workbook, name, headers)

    def write_aggregated_data(self, organisation, worksheet, data):

        worksheet.write(self.row_counter_engagement_aggregated_data, 0, organisation)
        worksheet.write(self.row_counter_engagement_aggregated_data, 1, 1)  # TODO: How do you count these ?
        worksheet.write(self.row_counter_engagement_aggregated_data, 2, data['total_members'])
        worksheet.write(self.row_counter_engagement_aggregated_data, 3, data['engagement_score_not_engaged'])
        worksheet.write(self.row_counter_engagement_aggregated_data, 4, data['engagement_score_little_engaged'])
        worksheet.write(self.row_counter_engagement_aggregated_data, 5, data['engagement_score_engaged'])
        worksheet.write(self.row_counter_engagement_aggregated_data, 6, data['engagement_score_very_engaged'])
        worksheet.write(self.row_counter_engagement_aggregated_data, 7, data['total_engaged'])
        worksheet.write(self.row_counter_engagement_aggregated_data, 8, data['total_engaged_percentage'])
        worksheet.write(self.row_counter_engagement_aggregated_data, 9, data['projects_realised'])
        worksheet.write(self.row_counter_engagement_aggregated_data, 10, data['projects_done'])
        worksheet.write(self.row_counter_engagement_aggregated_data, 11, data['donations_anonymous'])

        self.row_counter_engagement_aggregated_data += 1

    def generate_aggregated_data(self, data):

        aggregated_data = defaultdict(int)

        for _, entry in data.iteritems():
            engagement_score = self.get_engagement_score(entry)
            engagement_rating = self.get_engagement_rating(engagement_score)

            if engagement_rating == 'not engaged':
                aggregated_data['engagement_score_not_engaged'] += 1
            elif engagement_rating == 'little engaged':
                aggregated_data['engagement_score_little_engaged'] += 1
            elif engagement_rating == 'engaged':
                aggregated_data['engagement_score_engaged'] += 1
            elif engagement_rating == 'very engaged':
                aggregated_data['engagement_score_very_engaged'] += 1

        aggregated_data['total_members'] = Member.objects.all().count()

        aggregated_data['projects_realised'] = Project.objects.filter(status__slug='done-complete',
                                                                      created__gte=self.start_date,
                                                                      created__lt=self.end_date).count()
        aggregated_data['projects_done'] = Project.objects.filter(status__slug='done-incomplete',
                                                                  created__gte=self.start_date,
                                                                  created__lt=self.end_date).count()
        aggregated_data['donations_anonymous'] = Order.objects.filter(created__gte=self.start_date,
                                                                      created__lt=self.end_date,
                                                                      status='success',
                                                                      user__isnull=True).count()

        aggregated_data['total_engaged'] = aggregated_data['engagement_score_engaged'] + \
            aggregated_data['engagement_score_very_engaged']
        aggregated_data['total_engaged_percentage'] = (aggregated_data['total_engaged'] * 100) / \
            aggregated_data['total_members']

        return aggregated_data
