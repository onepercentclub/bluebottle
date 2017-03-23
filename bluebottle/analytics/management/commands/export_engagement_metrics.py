import argparse
import logging
from datetime import datetime

import xlsxwriter
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count, Sum
from django.utils import dateparse

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.members.models import Member

logger = logging.getLogger(__name__)

# TODO: Write the time frame (start_date and end_date) from the command line to the file


class Command(BaseCommand):
    help = 'Export the engagement metrics'

    row_counter_engagement_raw_data = 1
    row_counter_engagement_aggregated_data = 1

    @staticmethod
    def _validate_date(date_string):
        try:
            datetime.strptime(date_string, '%Y-%m-%d')
            return date_string
        except ValueError:
            msg = '{} is not a valid date or is not in the required date format YYYY-MM-DD'.format(date_string)
            raise argparse.ArgumentTypeError(msg)

    def add_arguments(self, parser):
        # TODO: Add arguments to select export destination
        # TODO: Make tenant selection interactive
        # TODO: Validate user entered tenant names
        parser.add_argument('--start', metavar='YYYY-MM-DD', action='store', dest='start', required=True,
                            type=self._validate_date, help="Start date (YYYY-MM-DD) for dump. UTC is the default \
                            time zone")

        parser.add_argument('--end', metavar='YYYY-MM-DD', action='store', dest='end', required=True,
                            type=self._validate_date,
                            help="End date (YYYY-MM-DD) for dump. UTC is the default time zone")

        parser.add_argument('--tenants', metavar='tenants', action='store', dest='tenants', required=False, nargs='*',
                            help="The names of the tenants to export")

    def write_aggregated_data(self, organisation, worksheet, data):

        total_engaged = data['engagement_score_engaged'] + data['engagement_score_very_engaged']
        total_engaged_percentage = (total_engaged * 100) / data['total_members']

        worksheet.write(self.row_counter_engagement_aggregated_data, 0, organisation)
        worksheet.write(self.row_counter_engagement_aggregated_data, 1, 1)  # TODO: How do you count these ?
        worksheet.write(self.row_counter_engagement_aggregated_data, 2, data['total_members'])
        worksheet.write(self.row_counter_engagement_aggregated_data, 3, data['engagement_score_not_engaged'])
        worksheet.write(self.row_counter_engagement_aggregated_data, 4, data['engagement_score_little_engaged'])
        worksheet.write(self.row_counter_engagement_aggregated_data, 5, data['engagement_score_engaged'])
        worksheet.write(self.row_counter_engagement_aggregated_data, 6, data['engagement_score_very_engaged'])
        worksheet.write(self.row_counter_engagement_aggregated_data, 7, total_engaged)
        worksheet.write(self.row_counter_engagement_aggregated_data, 8, total_engaged_percentage)

        self.row_counter_engagement_aggregated_data += 1

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
            worksheet.write(self.row_counter_engagement_raw_data, 10,
                            self.get_engagement_rating(entry['engagement_score']))

            self.row_counter_engagement_raw_data += 1

    @staticmethod
    def get_engagement_rating(score):

        if score == 0:
            return 'not engaged'
        elif score <= 4:
            return 'little engaged'
        elif 4 < score <= 8:
            return 'engaged'
        elif score > 8:
            return 'very engaged'

    @staticmethod
    def get_engagement_score(entry):
        return entry['comments'] * 1 + entry['votes'] * 2 + entry['donations'] * 4 + \
            entry['tasks'] + entry['fundraisers'] * 10 + entry['projects'] * 12

    def generate_engagement_aggregate_score(self, data):

        aggregated_data = {
            'engagement_score_not_engaged': 0,
            'engagement_score_little_engaged': 0,
            'engagement_score_engaged': 0,
            'engagement_score_very_engaged': 0
        }

        # TODO: Do we need to really iterate twice to get engagement aggregate score
        # TODO: Maybe try a different data structure integrated into raw_data
        for _, entry in data.iteritems():
            engagement_score = self.get_engagement_score(entry)
            engagement_rating = self.get_engagement_rating(engagement_score)

            if engagement_rating == 'not engaged':
                aggregated_data['engagement_score_not_engaged'] += 1
            elif engagement_rating == 'little engaged':
                aggregated_data['engagement_score_little_engaged'] += 1
            elif engagement_rating == ' engaged':
                aggregated_data['engagement_score_very_engaged'] += 1
            elif engagement_rating == 'very engaged':
                aggregated_data['engagement_score_very_engaged'] += 1

        return aggregated_data

    def generate_engagement_raw_scores(self, data):
        for _, entry in data.iteritems():
            entry['engagement_score'] = self.get_engagement_score(entry)
        return data

    @staticmethod
    def has_active_members(start_date, end_date):
        return True if Member.objects.filter(last_login__gte=start_date, last_login__lte=end_date).count() else False

    @staticmethod
    def initialize_worksheet(workbook, name, headers):

        worksheet = workbook.add_worksheet(name)
        for i, label in enumerate(headers):
            worksheet.write(0, i, label)

        return worksheet

    """ Dump engagement records for all tenants over a given date range """
    def handle(self, **options):
        start_date = dateparse.parse_datetime('{} 00:00:00+00:00'.format(options['start']))
        end_date = dateparse.parse_datetime('{} 23:59:59+00:00'.format(options['end']))
        tenants = set(options['tenants']) if options['tenants'] else None

        file_name = 'engagement_report_{}_{}_generated_{}.xlsx'\
            .format(start_date.strftime("%Y%m%d"),
                    end_date.strftime("%Y%m%d"),
                    datetime.now().strftime("%Y%m%d-%H%M%S"))

        with xlsxwriter.Workbook(file_name) as workbook:
            columns_engagement_raw_data = ('organisation', 'member id', 'comments', 'votes', 'donations',
                                           'fundraisers', 'projects', 'tasks', 'year_last_seen', 'engagement_score',
                                           'engagement_rating')

            columns_engagement_aggregated_data = ('organisation',
                                                  'total no. of platforms',
                                                  'total members',
                                                  'not engaged members (engagement score: 0)',
                                                  'little engaged members (engagement score: 1-3)',
                                                  'engaged members (engagement score: 4-8)',
                                                  'very engaged members (engagement score: >8)',
                                                  'total engaged members (engagement score: >4)',
                                                  '% total engaged members (engagement score: >4)'
                                                  )

            worksheet_engagement_raw_data = self.initialize_worksheet(workbook, 'Engagement Raw Data',
                                                                      columns_engagement_raw_data)
            worksheet_engagement_aggregated_data = self.initialize_worksheet(workbook, 'Engagement Aggregated Data',
                                                                             columns_engagement_aggregated_data)

            for client in Client.objects.all():
                if tenants is None or client.client_name in tenants:
                    connection.set_tenant(client)

                    with LocalTenant(client, clear_tenant=True):

                        raw_data = {}
                        logger.info('export tenant:{}'.format(client.client_name))

                        if self.has_active_members(start_date, end_date):
                            members = Member.objects.all()

                            for member in members:
                                raw_data[member.id] = {
                                    'year_last_seen': getattr(member.last_seen, 'year', ''),
                                    'comments': 0,
                                    'votes': 0,
                                    'donations': 0,
                                    'fundraisers': 0,
                                    'projects': 0,
                                    'tasks': 0,
                                    'engagement_score': 0
                                }

                            comments = Member.objects \
                                .filter(wallpost_wallpost__created__gte=start_date,
                                        wallpost_wallpost__created__lte=end_date)\
                                .annotate(total=Count('wallpost_wallpost'))\
                                .values('id', 'total')

                            for comment in comments:
                                # TODO: comment.id doesnt feel right. it should be comment.member_id
                                raw_data[comment['id']]['comments'] = comment['total']

                            votes = Member.objects\
                                .filter(vote__created__gte=start_date, vote__created__lte=end_date)\
                                .annotate(total=Count('vote'))\
                                .values('id', 'total')

                            for vote in votes:
                                # TODO: votes['id] doesnt feel right. it should be votes.member_id
                                raw_data[vote['id']]['votes'] = vote['total']

                            donations = Member.objects\
                                .filter(order__created__gte=start_date, order__created__lte=end_date,
                                        order__status="success", id__isnull=False)\
                                .annotate(total=Count('order'))\
                                .values('id', 'total')

                            for donation in donations:
                                # TODO: donation['id] doesnt feel right. it should be donation.member_id
                                raw_data[donation['id']]['donations'] = donation['total']

                            fundraisers = Member.objects\
                                .filter(fundraiser__created__gte=start_date, fundraiser__created__lte=end_date)\
                                .annotate(total=Count('fundraiser'))\
                                .values('id', 'total')

                            for fundraiser in fundraisers:
                                # TODO: fundraiser['id] doesnt feel right. it should be fundraiser.member_id
                                raw_data[fundraiser['id']]['fundraisers'] = fundraiser['total']

                            # TODO: Fix the project numbers to be correct
                            projects = Member.objects\
                                .filter(owner__created__gte=start_date, owner__created__lte=end_date)\
                                .annotate(total=Count('owner'))\
                                .values('id', 'total')

                            for project in projects:
                                # print(project)
                                pass

                            tasks = Member.objects\
                                .filter(tasks_taskmember_related__created__gte=start_date,
                                        tasks_taskmember_related__created__lte=end_date,
                                        tasks_taskmember_related__status='realized',
                                        tasks_taskmember_related__time_spent__gt=0)\
                                .annotate(total=Sum('tasks_taskmember_related__time_spent'))\
                                .values('id', 'total')

                            for task in tasks:
                                # TODO: task['id] doesnt feel right. it should be task.member_id
                                raw_data[task['id']]['tasks'] = task['total']

                            raw_data = self.generate_engagement_raw_scores(raw_data)

                            self.write_raw_data(client.client_name, worksheet_engagement_raw_data, raw_data)

                            aggregated_data = self.generate_engagement_aggregate_score(raw_data)
                            aggregated_data['total_members'] = members.count()
                            self.write_aggregated_data(client.client_name, worksheet_engagement_aggregated_data,
                                                       aggregated_data)
