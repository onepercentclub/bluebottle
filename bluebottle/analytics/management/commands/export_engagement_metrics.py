import argparse
import logging
from collections import defaultdict
from datetime import datetime

import xlsxwriter
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count, Sum
from django.utils import dateparse

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.members.models import Member
from bluebottle.orders.models import Order
from bluebottle.projects.models import Project

logger = logging.getLogger(__name__)


# TODO: Write the time frame (start_date and end_date) from the command line to the file
# NOTE: Score is a numeric value, Rating is a textual classification based on the score


class Command(BaseCommand):
    help = 'Export the engagement metrics'

    start_date = ''
    end_date = ''

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

    @staticmethod
    def has_active_members(start_date, end_date):

        return True if Member.objects.filter(last_login__gte=start_date, last_login__lte=end_date).count() else False

    @staticmethod
    def get_engagement_score(entry):

        return entry['comments'] * 1 + entry['votes'] * 2 + entry['donations'] * 4 + \
            entry['tasks'] + entry['fundraisers'] * 10 + entry['projects'] * 12

    @staticmethod
    def get_engagement_rating(score):

        if score == 0:
            return 'not engaged'
        elif 0 < score <= 4:
            return 'little engaged'
        elif 4 < score <= 8:
            return 'engaged'
        elif score > 8:
            return 'very engaged'

    @staticmethod
    def initialize_work_sheet(workbook, name, headers):
        worksheet = workbook.get_worksheet_by_name(name)
        if not worksheet:
            worksheet = workbook.add_worksheet(name)
            worksheet.write_row(0, 0, headers)
        return worksheet

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

    """ Dump engagement records for all tenants over a given date range """

    def handle(self, **options):

        self.start_date = dateparse.parse_datetime('{} 00:00:00+00:00'.format(options['start']))
        self.end_date = dateparse.parse_datetime('{} 23:59:59+00:00'.format(options['end']))
        tenants = set(options['tenants']) if options['tenants'] else None

        self.generate_engagement_data(tenants, self.start_date, self.end_date)

    def generate_engagement_data(self, tenants, start_date, end_date):

        file_name = 'engagement_report_{}_{}_generated_{}.xlsx'.format(start_date.strftime("%Y%m%d"),
                                                                       end_date.strftime("%Y%m%d"),
                                                                       datetime.now().strftime("%Y%m%d-%H%M%S"))

        with xlsxwriter.Workbook(file_name) as workbook:
            for client in Client.objects.all():
                if tenants is None or client.client_name in tenants:
                    connection.set_tenant(client)
                    with LocalTenant(client, clear_tenant=True):
                        logger.info('export tenant:{}'.format(client.client_name))
                        if self.has_active_members(self.start_date, self.end_date):
                            raw_data = self.generate_raw_data_worksheet(workbook, client.client_name)
                            self.generate_aggregated_data_worksheet(workbook, client.client_name, raw_data)

    def initialize_raw_data_worksheet(self, workbook):
        name = 'Engagement Raw Data'
        headers = ('organisation', 'member id', 'comments', 'votes', 'donations', 'fundraisers', 'projects', 'tasks',
                   'year_last_seen', 'engagement_score', 'engagement_rating')

        return self.initialize_work_sheet(workbook, name, headers)

    def generate_raw_data_worksheet(self, workbook, organisation):
        worksheet_raw_data = self.initialize_raw_data_worksheet(workbook)
        raw_data = {}
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

        raw_data = self.generate_comments_raw_data(raw_data)
        raw_data = self.generate_votes_raw_data(raw_data)
        raw_data = self.generate_donations_raw_data(raw_data)
        raw_data = self.generate_fundraisers_raw_data(raw_data)
        raw_data = self.generate_projects_raw_data(raw_data)
        raw_data = self.generate_tasks_raw_data(raw_data)
        raw_data = self.generate_raw_scores(raw_data)

        self.write_raw_data(organisation, worksheet_raw_data, raw_data)

        return raw_data

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
        worksheet.write(self.row_counter_engagement_aggregated_data, 9, data['projects_realised'])
        worksheet.write(self.row_counter_engagement_aggregated_data, 10, data['projects_done'])
        worksheet.write(self.row_counter_engagement_aggregated_data, 11, data['donations_anonymous'])

        self.row_counter_engagement_aggregated_data += 1

    def generate_aggregate_score(self, data):

        aggregated_data = defaultdict(int)

        # TODO: Do we need to really iterate twice to get engagement aggregate score
        # TODO: Maybe try a different data structure integrated into raw_data
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

        return aggregated_data

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

    def generate_raw_scores(self, data):
        for _, entry in data.iteritems():
            entry['engagement_score'] = self.get_engagement_score(entry)
        return data

    def generate_comments_raw_data(self, raw_data):
        comments = Member.objects \
            .filter(wallpost_wallpost__created__gte=self.start_date,
                    wallpost_wallpost__created__lte=self.end_date) \
            .annotate(total=Count('wallpost_wallpost')) \
            .values('id', 'total')

        for comment in comments:
            # TODO: comment.id doesnt feel right. it should be comment.member_id
            raw_data[comment['id']]['comments'] = comment['total']

        return raw_data

    def generate_votes_raw_data(self, raw_data):
        votes = Member.objects \
            .filter(vote__created__gte=self.start_date, vote__created__lte=self.end_date) \
            .annotate(total=Count('vote')) \
            .values('id', 'total')

        for vote in votes:
            # TODO: votes['id] doesnt feel right. it should be votes.member_id
            raw_data[vote['id']]['votes'] = vote['total']

        return raw_data

    def generate_donations_raw_data(self, raw_data):
        donations = Member.objects \
            .filter(order__created__gte=self.start_date, order__created__lte=self.end_date,
                    order__status="success", id__isnull=False) \
            .annotate(total=Count('order')) \
            .values('id', 'total')

        for donation in donations:
            # TODO: donation['id] doesnt feel right. it should be donation.member_id
            raw_data[donation['id']]['donations'] = donation['total']

        return raw_data

    def generate_fundraisers_raw_data(self, raw_data):
        fundraisers = Member.objects \
            .filter(fundraiser__created__gte=self.start_date, fundraiser__created__lte=self.end_date) \
            .annotate(total=Count('fundraiser')) \
            .values('id', 'total')

        for fundraiser in fundraisers:
            # TODO: fundraiser['id] doesnt feel right. it should be fundraiser.member_id
            raw_data[fundraiser['id']]['fundraisers'] = fundraiser['total']

        return raw_data

    def generate_projects_raw_data(self, raw_data):
        projects = Member.objects \
            .filter(owner__created__gte=self.start_date,
                    owner__created__lte=self.end_date,
                    owner__status__slug__in=['voting', 'voting-done', 'campaign',
                                             'to-be-continued', 'done-complete',
                                             'done-incomplete']) \
            .annotate(total=Count('owner')) \
            .values('id', 'total')

        for project in projects:
            raw_data[project['id']]['projects'] = project['total']

        return raw_data

    def generate_tasks_raw_data(self, raw_data):
        tasks = Member.objects \
            .filter(tasks_taskmember_related__created__gte=self.start_date,
                    tasks_taskmember_related__created__lte=self.end_date,
                    tasks_taskmember_related__status='realized',
                    tasks_taskmember_related__time_spent__gt=0) \
            .annotate(total=Sum('tasks_taskmember_related__time_spent')) \
            .values('id', 'total')

        for task in tasks:
            # TODO: task['id] doesnt feel right. it should be task.member_id
            raw_data[task['id']]['tasks'] = task['total']

        return raw_data

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

    def generate_aggregated_data_worksheet(self, workbook, organisation, raw_data):
        worksheet_aggregated_data = self.initialize_aggregated_data_worksheet(workbook)

        aggregated_data = self.generate_aggregate_score(raw_data)
        aggregated_data['total_members'] = Member.objects.all().count()

        projects_realised_count = Project.objects.filter(status__slug='done-complete',
                                                         created__gte=self.start_date,
                                                         created__lte=self.end_date).count()
        projects_done_count = Project.objects.filter(status__slug='done-incomplete',
                                                     created__gte=self.start_date,
                                                     created__lte=self.end_date).count()
        donations_anonymous_count = Order.objects.filter(created__gte=self.start_date,
                                                         created__lte=self.end_date,
                                                         status='success',
                                                         user__isnull=True).count()
        aggregated_data['projects_realised'] = projects_realised_count
        aggregated_data['projects_done'] = projects_done_count
        aggregated_data['donations_anonymous'] = donations_anonymous_count
        self.write_aggregated_data(organisation, worksheet_aggregated_data, aggregated_data)
