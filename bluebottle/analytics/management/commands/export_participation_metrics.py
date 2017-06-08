import logging
import pendulum

import xlsxwriter
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import dateparse

from .utils import validate_date, initialize_work_sheet, get_xls_file_name
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.members.models import Member
from bluebottle.statistics.statistics import Statistics

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Export the participation metrics'

    def __init__(self, **kwargs):
        super(Command, self).__init__(**kwargs)

        self.tenant = None

        self.all_tenants = []

        for client in Client.objects.all():
            self.all_tenants.append(client.client_name)

        self.start_date = ''
        self.end_date = ''

    def add_arguments(self, parser):

        parser.add_argument('--start', metavar='YYYY-MM-DD', action='store', dest='start', required=True,
                            type=validate_date, help="Start date (YYYY-MM-DD) for dump. UTC is the default \
                            time zone")

        parser.add_argument('--end', metavar='YYYY-MM-DD', action='store', dest='end', required=True,
                            type=validate_date,
                            help="End date (YYYY-MM-DD) for dump. UTC is the default time zone")

        parser.add_argument('--tenant', metavar='TENANT', action='store', dest='tenant', required=True,
                            choices=self.all_tenants, help="Name of the tenant to export")

    def handle(self, **options):
        self.tenant = options['tenant']

        self.start_date = dateparse.parse_datetime('{} 00:00:00+00:00'.format(options['start']))
        self.end_date = dateparse.parse_datetime('{} 00:00:00+00:00'.format(options['end']))

        self.generate_participation_xls()

    def generate_participation_xls(self):
        file_name = get_xls_file_name('participation_metrics', self.start_date, self.end_date)

        engagement_data = {}

        client = Client.objects.get(client_name=self.tenant)
        connection.set_tenant(client)

        with xlsxwriter.Workbook(file_name, {'default_date_format': 'dd/mm/yy', 'remove_timezone': True}) as workbook:
            with LocalTenant(client, clear_tenant=True):
                logger.info('export participation metrics - tenant:{} start_date:{} end_date:{}'
                            .format(self.tenant,
                                    self.start_date.strftime('%Y-%m-%d %H:%M:%S'),
                                    self.end_date.strftime('%Y-%m-%d %H:%M:%S')))
                self.generate_participants_worksheet(workbook)
                self.generate_totals_worksheet(workbook)
            # client_raw_data = self.generate_raw_data()
            # client_aggregated_data = self.generate_aggregated_data(client_raw_data)
            # engagement_data[client.client_name] = client_aggregated_data

        return engagement_data

    def generate_totals_worksheet(self, workbook):
        name = 'Totals - To Date'
        headers = ('Time Period',
                   'Year',
                   'Quarter',
                   'Month',
                   'Week',
                   'Start Date',
                   'End Date',
                   'Participants',
                   'Tasks - Successful',
                   'Projects - Successful',)
        worksheet = initialize_work_sheet(workbook, name, headers)

        format_metrics_header = workbook.add_format()
        format_metrics_header.set_bg_color('gray')
        format_metrics_header.set_bold()

        start_date = pendulum.instance(self.start_date)
        end_date = pendulum.instance(self.end_date)

        row = 1

        # By Year
        worksheet.write(row, 0, 'By Year', format_metrics_header)
        row += 1

        statistics_year_start = start_date.start_of('year').year
        statistics_year_end = end_date.end_of('year').year

        for year in range(statistics_year_start, statistics_year_end + 1):
            statistics_start_date = pendulum.create(year, 1, 1)
            statistics_end_date = pendulum.create(year + 1, 1, 1)

            logger.info('{} Yearly: {} - {}'.format(self.tenant, statistics_start_date, statistics_end_date))

            statistics = Statistics(start=statistics_start_date,
                                    end=statistics_end_date)
            worksheet.write(row, 0, 'Yearly')
            worksheet.write(row, 1, statistics_start_date.year)  # Year
            worksheet.write(row, 5, statistics_start_date)  # Start Date
            worksheet.write(row, 6, statistics_end_date.subtract(days=1))  # End Date
            # TODO: Double check defintion of participants
            worksheet.write(row, 7, statistics.participants)  # Participants
            # TODO: Double check definition of task successful
            worksheet.write(row, 8, statistics.tasks_realized)  # Tasks - Successful
            # TODO: Double check definition of projects successful
            worksheet.write(row, 9, statistics.projects_realized)  # Projects - Successful

            row += 1

        # By Month
        worksheet.write(row, 0, 'By Month', format_metrics_header)
        row += 1

        for year in range(statistics_year_start, statistics_year_end + 1):
            statistics_start_date = pendulum.create(year, 1, 1)
            for month in range(1, 13):
                statistics_end_date = pendulum.create(year, month, 1).end_of('month')

                if statistics_end_date < pendulum.now().add(months=1):
                    logger.info('{} Monthly: {} - {}'.format(self.tenant, statistics_start_date, statistics_end_date))

                    statistics = Statistics(start=statistics_start_date,
                                            end=statistics_end_date)
                    worksheet.write(row, 0, 'Monthly')  # Time period
                    worksheet.write(row, 1, statistics_start_date.year)  # Year
                    worksheet.write(row, 2, (statistics_end_date.subtract(days=1).month - 1) // 3 + 1)  # Quarter
                    worksheet.write(row, 3,
                                    statistics_end_date.subtract(days=1).format('MMMM', formatter='alternative'))
                    worksheet.write(row, 5, statistics_start_date)  # Start Date
                    worksheet.write(row, 6, statistics_end_date.subtract(days=1))  # End Date
                    # TODO: Double check defintion of participants
                    worksheet.write(row, 7, statistics.participants)  # Participants
                    # TODO: Double check definition of task successful
                    worksheet.write(row, 8, statistics.tasks_realized)  # Tasks - Successful
                    # TODO: Double check definition of projects successful
                    worksheet.write(row, 9, statistics.projects_realized)  # Projects - Successful

                    row += 1

        # By Week
        worksheet.write(row, 0, 'By Week', format_metrics_header)
        row += 1

        for year in range(statistics_year_start, statistics_year_end + 1):
            statistics_start_date = pendulum.create(year, 1, 1)
            time_period = pendulum.period(statistics_start_date, pendulum.create(year, 12, 31))
            for period in time_period.range('weeks'):
                statistics_end_date = period.end_of('week') \
                    if period.end_of('week') < statistics_start_date.end_of('year') \
                    else statistics_start_date.end_of('year')

                if statistics_end_date <= pendulum.now().add(weeks=1):
                    logger.info('{} Weekly: {} - {}'.format(self.tenant, statistics_start_date, statistics_end_date))
                    statistics = Statistics(start=statistics_start_date,
                                            end=statistics_end_date)
                    worksheet.write(row, 0, 'Weekly')  # Time Period
                    worksheet.write(row, 1, statistics_start_date.year)  # Year
                    worksheet.write(row, 2, (statistics_end_date.month - 1) // 3 + 1)  # Quarter
                    worksheet.write(row, 4, statistics_end_date.week_of_year)  # Week
                    worksheet.write(row, 5, statistics_start_date)  # Start Date
                    worksheet.write(row, 6, statistics_end_date.subtract(days=1))  # End Date
                    # TODO: Double check defintion of participants
                    worksheet.write(row, 7, statistics.participants)  # Participants
                    # TODO: Double check definition of task successful
                    worksheet.write(row, 8, statistics.tasks_realized)  # Tasks - Successful
                    # TODO: Double check definition of projects successful
                    worksheet.write(row, 9, statistics.projects_realized)  # Projects - Successful

                    row += 1

        chartsheet = workbook.add_chartsheet('Chart - Yearly Participants')
        chart = workbook.add_chart({'type': 'line'})
        chartsheet.set_chart(chart)
        # Configure second series. Note use of alternative syntax to define ranges.
        chart.add_series({
            'name': ['Totals - To Date', 0, 1],
            'categories': ['Totals - To Date', 2, 1, 5, 1],
            'values': ['Totals - To Date', 2, 7, 5, 7],
        })

        # Add a chart title and some axis labels.
        chart.set_title({'name': 'Yearly Participants'})
        chart.set_x_axis({'name': 'Year'})
        chart.set_y_axis({'name': 'Participants'})

        # Set an Excel chart style. Colors with white outline and shadow.
        chart.set_style(10)

    @staticmethod
    def generate_participants_worksheet(workbook):
        name = 'Participants - To Date'
        headers = ('Email Address',
                   'Date Joined',
                   'Year',
                   'Week Number')
        worksheet = initialize_work_sheet(workbook, name, headers)

        members = Member.objects.all().order_by('-date_joined')
        date_format = workbook.add_format({'num_format': 'dd/mm/yy', 'align': 'right'})
        for row, member in enumerate(members, 1):
            date_joined = pendulum.instance(member.date_joined)
            worksheet.write(row, 0, member.email)
            worksheet.write_datetime(row, 1, date_joined, date_format)
            worksheet.write(row, 2, date_joined.year)
            worksheet.write(row, 3, date_joined.week_of_year)
