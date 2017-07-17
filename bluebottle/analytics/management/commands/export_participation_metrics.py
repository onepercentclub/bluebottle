import logging
from collections import namedtuple
import pendulum
import xlsxwriter
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import dateparse

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.statistics.statistics import Statistics
from .utils import initialize_work_sheet, get_xls_file_name
from xlsxwriter.utility import xl_rowcol_to_cell

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Export the participation metrics per tenant'

    def __init__(self, **kwargs):
        super(Command, self).__init__(**kwargs)

        self.tenant = None
        self.all_tenants = []
        for client in Client.objects.all():
            self.all_tenants.append(client.client_name)

        self.start_date = ''
        self.end_date = ''

    @staticmethod
    def setup_workbook_formatters(workbook):
        formatters = dict()

        formatters['format_metrics_header'] = workbook.add_format()
        formatters['format_metrics_header'].set_bg_color('gray')
        formatters['format_metrics_header'].set_bold()

        return formatters

    @staticmethod
    def create_participants_worksheet(workbook, year):
        name = 'Participants - Year {}'.format(year)
        headers = ('Email Address',
                   'Participation Date',
                   'Year',
                   'Week Number')
        return initialize_work_sheet(workbook, name, headers)

    @staticmethod
    def create_totals_worksheet(workbook, year):
        name = 'Totals - Year {}'.format(year)
        headers = ('Time Period',  # 0
                   'Year',  # 1
                   'Quarter',  # 2
                   'Month',  # 3
                   'Week',  # 4
                   'Start Date',  # 5
                   'End Date',  # 6
                   'Participants',  # 7
                   'Participant Growth',  # 8
                   'Projects - Successful',  # 9
                   'Running - Project Status',  # 10
                   'Submitted - Project Status',  # 11
                   'Draft - Project Status',  # 12
                   'Needs Work - Project Status',  # 13
                   'Done - Project Status',  # 14
                   'Realized - Project Status',  # 15
                   'Rejected/ Cancelled - Project Status',  # 16
                   'NORAM - Project Location Group',  # 17
                   'EMEA - Project Location Group',  # 18
                   'HQ - Project Location Group',  # 19
                   'APAC - Project Location Group',  # 20
                   'LATAM - Project Location Group',  # 21
                   'Tasks - Successful',  # 22
                   'Tasks - Total',  # 23
                   'Tasks - Open',  # 24
                   'Tasks - Running',  # 25
                   'Tasks - Realised',  # 26
                   'Tasks - Done (Closed)'  # 27
                   )
        return initialize_work_sheet(workbook, name, headers)

    @staticmethod
    def get_yearly_quarter(date):
        return (date.subtract(days=1).month - 1) // 3 + 1

    @staticmethod
    def get_month_name(date):
        return date.subtract(days=1).format('MMMM', formatter='alternative')

    def add_arguments(self, parser):

        parser.add_argument('--start-year', metavar='YYYY', action='store', dest='start', required=True,
                            type=int, help="Start Year (YYYY) for dump. UTC is the default time zone")

        parser.add_argument('--end-year', metavar='YYYY', action='store', dest='end', required=True,
                            type=int,
                            help="End Year (YYYY) for dump. UTC is the default time zone")

        parser.add_argument('--tenant', metavar='TENANT', action='store', dest='tenant', required=True,
                            choices=self.all_tenants, help="Name of the tenant to export")

    def handle(self, **options):
        self.tenant = options['tenant']
        self.start_date = dateparse.parse_datetime('{}-01-01 00:00:00+00:00'.format(options['start']))
        self.end_date = dateparse.parse_datetime('{}-01-01 00:00:00+00:00'.format(options['end']))

        self.generate_participation_xls()

    def generate_participation_xls(self):
        file_name = get_xls_file_name('participation_metrics_{}'.format(self.tenant), self.start_date, self.end_date)

        engagement_data = {}

        client = Client.objects.get(client_name=self.tenant)
        connection.set_tenant(client)

        with xlsxwriter.Workbook(file_name, {'default_date_format': 'dd/mm/yy', 'remove_timezone': True}) as workbook:
            with LocalTenant(client, clear_tenant=True):
                logger.info('export participation metrics - tenant:{} start_date:{} end_date:{}'
                            .format(self.tenant,
                                    self.start_date.strftime('%Y-%m-%d %H:%M:%S'),
                                    self.end_date.strftime('%Y-%m-%d %H:%M:%S')))
                self.generate_totals_worksheet(workbook)

        return engagement_data

    def write_stats(self, worksheet, row, statistic_type, start_date, end_date):
        statistics = Statistics(start=start_date, end=end_date)
        worksheet.write(row, 0, statistic_type.capitalize())  # Time Period
        worksheet.write(row, 1, start_date.year)  # Year
        worksheet.write(row, 5, start_date)  # Start Date
        worksheet.write(row, 6, end_date.subtract(days=1))  # End Date
        worksheet.write(row, 7, statistics.participants)  # Participants
        worksheet.write_formula(xl_rowcol_to_cell(row, 8),
                                '=IF(ISBLANK({}),0,{}-{})'.format(xl_rowcol_to_cell(row - 1, 7),
                                                                  xl_rowcol_to_cell(row, 7),
                                                                  xl_rowcol_to_cell(row - 1, 7)))  # Participants Growth
        worksheet.write(row, 9, statistics.projects_successful)  # Projects - Successful
        worksheet.write(row, 10, statistics.projects_running)  # Projects - Running
        worksheet.write(row, 11, statistics.projects_submitted)  # Projects - Submitted
        worksheet.write(row, 12, statistics.projects_draft)  # Projects - Draft
        worksheet.write(row, 13, statistics.projects_needs_work)  # Projects - Needs Work
        worksheet.write(row, 14, statistics.projects_done)  # Projects - Done
        worksheet.write(row, 15, statistics.projects_realized)  # Projects - Realized
        worksheet.write(row, 16, statistics.projects_rejected_cancelled)  # Projects - Rejected / Cancelled
        # TODO: DO NOT use hard coded location_group values
        worksheet.write(row, 17, len(statistics.get_projects_by_location_group('NORAM (North America)')))
        worksheet.write(row, 18, len(statistics.get_projects_by_location_group('EMEA (Europe, Middle East & Africa)')))
        worksheet.write(row, 19, len(statistics.get_projects_by_location_group('HQ (Amsterdam)')))
        worksheet.write(row, 20, len(statistics.get_projects_by_location_group('APAC (Asia Pacific)')))
        worksheet.write(row, 21, len(statistics.get_projects_by_location_group('LATAM (Latin America)')))
        worksheet.write(row, 22, statistics.tasks_realized)  # Tasks - Successful
        worksheet.write(row, 23, statistics.tasks_total)  # Tasks - Total
        worksheet.write(row, 24, statistics.tasks_open)  # Tasks - Open
        worksheet.write(row, 25, statistics.tasks_running)  # Tasks - Running
        worksheet.write(row, 26, statistics.tasks_realized)  # Tasks - Realised
        worksheet.write(row, 27, statistics.tasks_done)  # Tasks - Done

        if statistic_type == 'weekly':
            worksheet.write(row, 2, self.get_yearly_quarter(end_date))  # Quarter
            worksheet.write(row, 4, end_date.week_of_year)  # Week
        elif statistic_type == 'monthly':
            worksheet.write(row, 2, self.get_yearly_quarter(end_date))  # Quarter
            worksheet.write(row, 3, self.get_month_name(end_date))  # Month

    @staticmethod
    def create_monthly_chart(workbook, data, title):
        chartsheet = workbook.add_chartsheet('YoY Monthly {}'.format(title))
        chart = workbook.add_chart({'type': 'line'})
        chartsheet.set_chart(chart)

        for item in data:
            chart.add_series({
                'name': item['chart_name_coordinates'],
                'categories': item['chart_categories_coordinates'],
                'values': item['chart_values_coordinates'],
                'marker': {'type': 'circle'},
            })

        # Add a chart title and axis labels.
        chart.set_title({'name': 'Monthly {}s'.format(title)})
        chart.set_x_axis({'name': 'Month'})
        chart.set_y_axis({'name': '{}s'.format(title)})

        # Set an Excel chart style. Colors with white outline and shadow.
        chart.set_style(10)

        return chart

    @staticmethod
    def create_chart_data(worksheet, name_coords, catergories_coords, values_coords):
        data = dict()
        data['chart_name_coordinates'] = [worksheet.get_name(), name_coords.row, name_coords.column]
        data['chart_categories_coordinates'] = [worksheet.get_name(), catergories_coords.row, catergories_coords.column]
        data['chart_values_coordinates'] = [worksheet.get_name(), values_coords.row, values_coords.column]

        return data

    def generate_totals_worksheet(self, workbook):

        formatters = self.setup_workbook_formatters(workbook)

        start_date = pendulum.instance(self.start_date)
        end_date = pendulum.instance(self.end_date)

        statistics_year_start = start_date.start_of('year').year
        statistics_year_end = end_date.end_of('year').year

        Cell = namedtuple('Cell', ['row', 'column'])

        chart_participant_monthly_data = []
        chart_task_monthly_data = []
        chart_project_monthly_data = []

        for year in range(statistics_year_start, statistics_year_end + 1):

            statistics_start_date = pendulum.create(year, 1, 1)
            statistics_end_date = pendulum.create(year + 1, 1, 1)

            # Worksheet for Participants by Year
            participant_worksheet = self.create_participants_worksheet(workbook, year)
            statistics = Statistics(start=statistics_start_date, end=statistics_end_date)
            participants = statistics.participant_details()
            for row, participant in enumerate(participants, 1):
                participation_date = pendulum.instance(participant['action_date'])
                participant_worksheet.write(row, 0, participant['email'])
                participant_worksheet.write_datetime(row, 1, participation_date)
                participant_worksheet.write(row, 2, participation_date.year)
                participant_worksheet.write(row, 3, participation_date.week_of_year)

            # Worksheet for Totals by Year
            worksheet = self.create_totals_worksheet(workbook, year)

            # Generate data by year
            logger.info('tenant:{} Yearly: start_date:{} - end_date:{}'.format(self.tenant, statistics_start_date,
                                                                               statistics_end_date))

            row = 1
            worksheet.write(row, 0, 'By Year', formatters['format_metrics_header'])

            row += 1
            self.write_stats(worksheet=worksheet, row=row, statistic_type='yearly',
                             start_date=statistics_start_date, end_date=statistics_end_date)

            # Generate data by month
            row += 1
            worksheet.write(row, 0, 'By Month', formatters['format_metrics_header'])

            row += 1
            chart_participant_data = self.create_chart_data(worksheet,
                                                            name_coords=Cell(row=row, column=1),
                                                            catergories_coords=Cell(row=row, column=3),
                                                            values_coords=Cell(row=row, column=7),
                                                            )
            chart_project_data = self.create_chart_data(worksheet,
                                                        name_coords=Cell(row=row, column=1),
                                                        catergories_coords=Cell(row=row, column=3),
                                                        values_coords=Cell(row=row, column=9),
                                                        )
            chart_task_data = self.create_chart_data(worksheet,
                                                     name_coords=Cell(row=row, column=1),
                                                     catergories_coords=Cell(row=row, column=3),
                                                     values_coords=Cell(row=row, column=22),
                                                     )

            statistics_start_date = pendulum.create(year, 1, 1)
            for month in range(1, 13):
                statistics_end_date = pendulum.create(year, month, 1).end_of('month')

                if statistics_end_date < pendulum.now().add(months=1):
                    logger.info(
                        'tenant:{} Monthly: start_date:{} - end_date:{}'.format(self.tenant, statistics_start_date,
                                                                                statistics_end_date))
                    self.write_stats(worksheet=worksheet, row=row, statistic_type='monthly',
                                     start_date=statistics_start_date, end_date=statistics_end_date)

                    row += 1

            chart_participant_data['chart_categories_coordinates'].extend([row - 1, 3])
            chart_participant_data['chart_values_coordinates'].extend([row - 1, 7])
            chart_participant_monthly_data.append(chart_participant_data)

            chart_project_data['chart_categories_coordinates'].extend([row - 1, 3])
            chart_project_data['chart_values_coordinates'].extend([row - 1, 9])
            chart_project_monthly_data.append(chart_project_data)

            chart_task_data['chart_categories_coordinates'].extend([row - 1, 3])
            chart_task_data['chart_values_coordinates'].extend([row - 1, 22])
            chart_task_monthly_data.append(chart_task_data)

            # Generate data by week
            worksheet.write(row, 0, 'By Week', formatters['format_metrics_header'])
            row += 1

            statistics_start_date = pendulum.create(year, 1, 1)
            time_period = pendulum.period(statistics_start_date, pendulum.create(year, 12, 31))
            for period in time_period.range('weeks'):

                statistics_end_date = period.end_of('week') \
                    if period.end_of('week') < statistics_start_date.end_of('year') \
                    else statistics_start_date.end_of('year')

                if statistics_end_date <= pendulum.now().add(weeks=1):
                    logger.info(
                        'tenant:{} Weekly: start_date:{} - end_date:{}'.format(self.tenant, statistics_start_date,
                                                                               statistics_end_date))
                    self.write_stats(worksheet=worksheet, row=row, statistic_type='weekly',
                                     start_date=statistics_start_date, end_date=statistics_end_date)

                    row += 1

        self.create_monthly_chart(workbook, chart_participant_monthly_data, 'Participant')
        self.create_monthly_chart(workbook, chart_task_monthly_data, 'Task')
        self.create_monthly_chart(workbook, chart_project_monthly_data, 'Project')
