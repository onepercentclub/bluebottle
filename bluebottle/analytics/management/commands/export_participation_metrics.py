import logging
from collections import namedtuple, OrderedDict, defaultdict

import pendulum
import xlsxwriter
from django.core.management.base import BaseCommand
from django.db import connection
from xlsxwriter.utility import xl_rowcol_to_cell

from bluebottle.bb_projects.models import ProjectPhase, ProjectTheme
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.geo.models import LocationGroup
from bluebottle.statistics.participation import Statistics
from bluebottle.tasks.models import Task, TaskMember
from bluebottle.utils.email_backend import send_mail
from .utils import initialize_work_sheet
import tempfile
import os

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Export the participation metrics per tenant'

    colors = {
        'projects': '',
        'tasks': '',
        'task_members': ''
    }

    RowData = namedtuple('RowData', ['metric', 'definition', 'hide_column', 'is_formula'])

    def __init__(self, **kwargs):
        super(Command, self).__init__(**kwargs)

        self.tenant = None
        self.to_email = None
        self.file_path = None

        self.all_tenants = [client.client_name for client in Client.objects.all()]

        self.start_date = None
        self.end_date = None

        self.charts = defaultdict(dict)

        self.yearly_statistics_row_start = 1
        self.monthly_statistics_row_start = 4
        self.monthly_statistics_row_end = None
        self.weekly_statistics_row_start = 17
        self.weekly_statistics_row_end = None

    @staticmethod
    def setup_workbook_formatters(workbook):
        formatters = dict()

        formatters['metrics_header'] = workbook.add_format()
        formatters['metrics_header'].set_bg_color('gray')
        formatters['metrics_header'].set_bold()

        formatters['project_status'] = workbook.add_format()
        formatters['project_status'].set_bg_color('gray')

        formatters['task_status'] = workbook.add_format()
        formatters['task_status'].set_bg_color('gray')

        formatters['task_member_status'] = workbook.add_format()
        formatters['task_member_status'].set_bg_color('gray')

        return formatters

    @staticmethod
    def create_participants_worksheet(workbook, year):
        name = 'Participants - {}'.format(year)
        headers = ('Email Address',
                   'Participation Date',
                   'Year',
                   'Week Number')

        return initialize_work_sheet(workbook, name, headers)

    @staticmethod
    def create_totals_worksheet(workbook, year):
        name = 'Totals - {}'.format(year)
        return initialize_work_sheet(workbook, name)

    @staticmethod
    def create_location_segmentation_worksheet(workbook, year):
        name = 'Location Segmentation - {}'.format(year)
        return initialize_work_sheet(workbook, name)

    @staticmethod
    def create_theme_segmentation_worksheet(workbook, year):
        name = 'Theme Segmentation - {}'.format(year)
        return initialize_work_sheet(workbook, name)

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

        parser.add_argument('--email', metavar='EMAIL', action='store', dest='email', required=False,
                            help="Email of the contact person")

    def handle(self, **options):
        self.tenant = options['tenant']
        self.to_email = options['email']
        self.start_date = pendulum.create(options['start'], 1, 1, 0, 0, 0)
        self.end_date = pendulum.create(options['end'], 12, 31, 23, 59, 59)

        self.generate_participation_xls()

    def generate_participation_xls(self):
        now = pendulum.now()
        file_name = 'participation_metrics_{}_{}_{}_generated_{}_{}.xlsx'.format(self.tenant,
                                                                                 self.start_date.to_date_string(),
                                                                                 self.end_date.to_date_string(),
                                                                                 now.to_date_string(),
                                                                                 now.int_timestamp)

        client = Client.objects.get(client_name=self.tenant)
        connection.set_tenant(client)

        self.file_path = os.path.join(tempfile.gettempdir(), file_name)
        with xlsxwriter.Workbook(self.file_path,
                                 {'default_date_format': 'dd/mm/yy', 'remove_timezone': True}) as workbook:
            with LocalTenant(client, clear_tenant=True):
                logger.info('export participation metrics - tenant:{} start_date:{} end_date:{}'
                            .format(self.tenant,
                                    self.start_date.to_iso8601_string(),
                                    self.end_date.to_iso8601_string())
                            )
                logger.info('file path: {}'.format(self.file_path))
                self.generate_participants_worksheet(workbook)
                self.generate_worksheet(workbook, 'aggregated')
                self.generate_worksheet(workbook, 'location_segmentation')
                self.generate_worksheet(workbook, 'theme_segmentation')

        if self.to_email:
            with open(self.file_path, 'r') as f:
                User = namedtuple('User', 'email')
                user = User(email=self.to_email)
                send_mail(template_name='participation_metrics_email',
                          subject='Participation Metrics',
                          to=user,
                          attachments=[(file_name, f.read())],
                          connection=connection)

    @staticmethod
    def get_column_for_metric(row_data, metric_name):
        return row_data.keys().index(metric_name)

    @staticmethod
    def create_monthly_charts(workbook, chart_data):
        for title, multi_year_data in chart_data.iteritems():
            chartsheet = workbook.add_chartsheet('{}'.format(title))
            chart = workbook.add_chart({'type': 'line'})
            chart.set_title({'name': '{}'.format(title)})
            chart.set_x_axis({'name': 'Month'})
            chart.set_y_axis({'name': 'Total'})
            chart.set_style(10)
            for year, yearly_data in multi_year_data.iteritems():
                chart.add_series({
                    'name': yearly_data['name_coords'],
                    'categories': yearly_data['categories_coords'],
                    'values': yearly_data['values_coords'],
                    'marker': {'type': 'circle'}
                })
            chartsheet.set_chart(chart)

    def get_chart_data(self, worksheet, column_year, column_month, column_total):
        return {
            'name_coords': [worksheet.get_name(),
                            self.monthly_statistics_row_start,
                            column_year],
            'categories_coords': [worksheet.get_name(),
                                  self.monthly_statistics_row_start,
                                  column_month,
                                  self.monthly_statistics_row_end,
                                  column_month],
            'values_coords': [worksheet.get_name(),
                              self.monthly_statistics_row_start,
                              column_total,
                              self.monthly_statistics_row_end,
                              column_total]
        }

    @staticmethod
    def get_growth_formula(row, col):
        return '=IF(ISBLANK({}),0,{}-{})'.format(xl_rowcol_to_cell(row - 1, col),
                                                 xl_rowcol_to_cell(row, col),
                                                 xl_rowcol_to_cell(row - 1, col))

    @staticmethod
    def write_headers(worksheet, row_data):
        for column, data in enumerate(row_data.iteritems()):
            worksheet.write(0, column, data[0])
            worksheet.write_comment(0, column, data[1].definition)
            if data[1].hide_column:
                worksheet.set_column(column, column, None, None, {'hidden': 1})

    @staticmethod
    def write_row(worksheet, row, row_data):
        for column, data in enumerate(row_data.iteritems()):
            metric_value = data[1].metric
            is_formula = data[1].is_formula
            if is_formula:
                worksheet.write_formula(row, column, metric_value)
            else:
                worksheet.write(row, column, metric_value)

    def create_time_row_data(self, worksheet, row_data, statistic_type, end_date):
        row_data['Time Period'] = self.RowData(metric=statistic_type.capitalize(),
                                               is_formula=False,
                                               hide_column=False,
                                               definition='Time period for the statistics.')

        row_data['Year'] = self.RowData(metric=end_date.year,
                                        is_formula=False,
                                        hide_column=False,
                                        definition='The year associated with the end date.')
        column_year = row_data.keys().index('Year')

        row_data['Quarter'] = self.RowData(
            metric=self.get_yearly_quarter(end_date) if statistic_type in ['weekly', 'monthly'] else '',
            is_formula=False,
            hide_column=False,
            definition='The yearly quarter associated with the end date.')

        row_data['Month'] = self.RowData(metric=self.get_month_name(end_date) if statistic_type == 'monthly' else '',
                                         is_formula=False,
                                         hide_column=False,
                                         definition='The calendar month associated with the end date.')
        column_month = row_data.keys().index('Month')

        row_data['Week'] = self.RowData(metric=end_date.week_of_year if statistic_type == 'weekly' else '',
                                        is_formula=False,
                                        hide_column=False,
                                        definition='The ISO calendar week associated with the end date.')

        row_data['End Date'] = self.RowData(metric=end_date.subtract(days=1),
                                            is_formula=False,
                                            hide_column=False,
                                            definition='The end date for the current statistic period.')

        # Freeze panes after this column for easy viewing
        worksheet.freeze_panes(1, row_data.keys().index('End Date') + 1)

        return column_year, column_month

    def write_total_stats(self, worksheet, row, statistic_type, start_date, end_date):
        statistics = Statistics(start=start_date, end=end_date)

        row_data = OrderedDict()

        column_year, column_month = self.create_time_row_data(worksheet, row_data, statistic_type, end_date)

        # Participant Statistics
        row_data['Participants'] = self.RowData(metric=statistics.participants_count,
                                                is_formula=False,
                                                hide_column=False,
                                                definition='Participants are defined as project initiators of a '
                                                           'project (running, done or realised), task members (that '
                                                           'applied for, got accepted for, or realised a task) or task '
                                                           'initiators. If a member is one of the three (e.g. a '
                                                           'project initiator or a task member or a task initiator), '
                                                           'they are counted as one participant.')
        column_participants = row_data.keys().index('Participants')

        row_data['Participants Total Growth'] = self.RowData(
            metric=self.get_growth_formula(row, column_participants),
            is_formula=True,
            hide_column=False,
            definition='Growth of participants for the defined time period.')

        # NOTE: Temporary Participant Statistics considering only task members with status realized
        row_data['Participants With Task Member Status Realized'] = self.RowData(
            metric=statistics.participants_count_with_only_task_members_realized,
            is_formula=False,
            hide_column=False,
            definition='Participants are defined as project initiators of a project '
                       '(running, done or realised), task members who realised a task or task initiators. '
                       'If a member is one of the three (e.g. a project initiator or a '
                       'task member or a task initiator), they are counted as one '
                       'participant.')
        column_participants_task_member = row_data.keys().index('Participants With Task Member Status Realized')

        row_data['Participants With Task Member Status Realized Growth'] = self.RowData(
            metric=self.get_growth_formula(row, column_participants_task_member),
            is_formula=True,
            hide_column=False,
            definition='')

        # Projects Statistics
        row_data['Projects Total'] = self.RowData(
            metric=statistics.projects_total,
            is_formula=False,
            hide_column=False,
            definition='Total count of projects in all known statuses which were created before the end date.')
        column_projects_total = row_data.keys().index('Projects Total')

        row_data['Projects Total Growth'] = self.RowData(
            metric=self.get_growth_formula(row, column_projects_total),
            is_formula=True,
            hide_column=False,
            definition='Growth of projects for the defined time period.')

        for project_phase in ProjectPhase.objects.all():
            row_data['Project Status - {}'.format(project_phase.name)] = self.RowData(
                metric=statistics.get_projects_count_by_last_status([project_phase.slug]),
                is_formula=False,
                hide_column=False,
                definition='Total count of projects with the status, {}, which were created '
                           'before the end date.'.format(project_phase.name))
            column_project_status = self.get_column_for_metric(row_data,
                                                               'Project Status - {}'.format(project_phase.name))

            row_data['Projects Status - {} Growth'.format(project_phase.name)] = self.RowData(
                metric=self.get_growth_formula(row, column_project_status),
                is_formula=True,
                hide_column=True,
                definition='Growth of projects for the defined status ({}) within the time period.'
                           .format(project_phase.name))

        for location_group in LocationGroup.objects.all():
            row_data['Location - {}'.format(location_group.name)] = self.RowData(
                metric=len(statistics.get_projects_by_location_group(location_group.name)),
                is_formula=False,
                hide_column=False,
                definition='Total count of projects with the location, {}, which were created '
                           'before the end date.'.format(location_group.name))
            column_location_group = self.get_column_for_metric(row_data, 'Location - {}'.format(location_group.name))

            row_data['Location - {} Growth'.format(location_group.name)] = self.RowData(
                metric=self.get_growth_formula(row, column_location_group),
                is_formula=True,
                hide_column=True,
                definition='Growth rate of projects per location')

        for theme in ProjectTheme.objects.all():
            row_data['Theme - {}'.format(theme.name)] = self.RowData(
                metric=statistics.get_projects_count_by_theme(theme.slug),
                is_formula=False,
                hide_column=False,
                definition='Total count of projects with the theme, {}, which were created '
                           'before the end date.'.format(theme.name))
            column_project_theme = self.get_column_for_metric(row_data, 'Theme - {}'.format(theme.name))

            row_data['Theme - {} Growth'.format(theme.name)] = self.RowData(
                metric=self.get_growth_formula(row, column_project_theme),
                is_formula=True,
                hide_column=True,
                definition='Growth rate of projects per theme')

        # Tasks Statistics
        row_data['Tasks Total'] = self.RowData(
            metric=statistics.tasks_total,
            is_formula=False,
            hide_column=False,
            definition='Total count of task in all statuses which were created before the end date.')
        column_task_total = row_data.keys().index('Tasks Total')

        row_data['Tasks Total Growth'] = self.RowData(
            metric=self.get_growth_formula(row, column_task_total),
            is_formula=True,
            hide_column=False,
            definition='Growth of tasks for the defined time period.')

        for task_status, label in Task.TaskStatuses.choices:
            row_data['Task Status - {}'.format(label)] = self.RowData(
                metric=statistics.get_tasks_count_by_last_status([task_status]),
                is_formula=False,
                hide_column=False,
                definition='Total count of task with the status, {}, '
                           'which were created before the end date.'.format(label))
            column_task_status = row_data.keys().index('Task Status - {}'.format(label))

            row_data['Tasks Status - {} Growth'.format(label)] = self.RowData(
                metric=self.get_growth_formula(row, column_task_status),
                is_formula=True,
                hide_column=True,
                definition='Growth of tasks for the defined status within the time period.')

        # Task Member Statistics
        row_data['Task Members Total'] = self.RowData(
            metric=statistics.task_members_total,
            is_formula=False,
            hide_column=False,
            definition='Total count of task members in all statuses which were created before the end date.')
        column_task_member_total = row_data.keys().index('Task Members Total')

        row_data['Task Members Total Growth'] = self.RowData(
            metric=self.get_growth_formula(row, column_task_member_total),
            is_formula=True,
            hide_column=False,
            definition='Growth of tasks for the defined time period.')

        for task_member_status, label in TaskMember.TaskMemberStatuses.choices:
            row_data['Task Member Status - {}'.format(label)] = self.RowData(
                metric=statistics.get_task_members_count_by_last_status([task_member_status]),
                is_formula=False,
                hide_column=False,
                definition='Total count of task members with the status, {}, '
                           'which were created before the end date.'.format(label))
            column_task_member_status = row_data.keys().index('Task Member Status - {}'.format(label))

            row_data['Task Member Status - {} Growth'.format(label)] = self.RowData(
                metric=self.get_growth_formula(row, column_task_member_status),
                is_formula=True,
                hide_column=True,
                definition='Growth of task members per status within the defined time period')

        row_data['Unconfirmed Task Members Total'] = self.RowData(
            metric=statistics.unconfirmed_task_members,
            is_formula=False,
            hide_column=False,
            definition='Total number of task members with the status - accepted, before the time period end date, '
                       'belonging to a task that is 10 days or more beyond its task deadline')

        row_data['Tasks with Unconfirmed Task Members Total'] = self.RowData(
            metric=statistics.unconfirmed_task_members_task_count,
            is_formula=False,
            hide_column=False,
            definition='Total number of unique tasks belonging to the unconfirmed task members.')

        # Write Headers, if the first row is being written
        if row == 2:
            self.write_headers(worksheet, row_data)

        # Write row data
        self.write_row(worksheet, row, row_data)

        # Generate YoY Monthly Charts
        if statistic_type == 'monthly':
            self.charts['Participants Total Growth'][end_date.year] = self.get_chart_data(
                worksheet=worksheet,
                column_year=column_year,
                column_month=column_month,
                column_total=column_participants
            )

            self.charts['Projects Total Growth'][end_date.year] = self.get_chart_data(
                worksheet=worksheet,
                column_year=column_year,
                column_month=column_month,
                column_total=column_projects_total
            )

            self.charts['Tasks Total Growth'][end_date.year] = self.get_chart_data(
                worksheet=worksheet,
                column_year=column_year,
                column_month=column_month,
                column_total=column_task_total
            )

            self.charts['Task Members Total Growth'][end_date.year] = self.get_chart_data(
                worksheet=worksheet,
                column_year=column_year,
                column_month=column_month,
                column_total=column_task_member_total
            )

    def write_theme_segmentation_stats(self, worksheet, row, statistic_type, start_date, end_date):
        statistics = Statistics(start=start_date, end=end_date)

        row_data = OrderedDict()

        self.create_time_row_data(worksheet, row_data, statistic_type, end_date)

        for theme in ProjectTheme.objects.all():
            # Project Status Statistics
            for project_phase in ProjectPhase.objects.all():
                row_data['Theme - {} / Project Status - {}'.format(theme.name, project_phase.name)] = \
                    self.RowData(metric=statistics.get_projects_status_count_by_theme(theme.slug, [project_phase.slug]),
                                 is_formula=False,
                                 hide_column=False,
                                 definition='Total count of projects with the theme - {} and project status - {} which '
                                            'were created before the end date.'
                                            .format(theme.name, project_phase.name))

        # Write Headers, if the first row is being written
        if row == 2:
            self.write_headers(worksheet, row_data)

        # Write row data
        self.write_row(worksheet, row, row_data)

    def write_location_segmentation_stats(self, worksheet, row, statistic_type, start_date, end_date):
        statistics = Statistics(start=start_date, end=end_date)

        row_data = OrderedDict()

        self.create_time_row_data(worksheet, row_data, statistic_type, end_date)

        for location_group in LocationGroup.objects.all():
            # Project Status Statistics
            for project_phase in ProjectPhase.objects.all():
                row_data['Location - {} / Project Status - {}'.format(location_group.name, project_phase.name)] = \
                    self.RowData(metric=statistics.get_projects_status_count_by_location_group(location_group.name,
                                                                                               [project_phase.slug]),
                                 is_formula=False,
                                 hide_column=False,
                                 definition='Total count of projects with the location - {} and project status - {} '
                                            'which were created before the end date.'
                                            .format(location_group.name, project_phase.name))

        # Write Headers, if the first row is being written
        if row == 2:
            self.write_headers(worksheet, row_data)

        # Write row data
        self.write_row(worksheet, row, row_data)

    def generate_participants_worksheet(self, workbook):
        for year in range(self.start_date.year, self.end_date.year + 1):
            statistics_start_date = pendulum.create(year, 1, 1, 0, 0, 0)
            statistics_end_date = pendulum.create(year, 12, 31, 23, 59, 59)
            statistics = Statistics(start=statistics_start_date, end=statistics_end_date)

            logger.info('tenant:{} Participants Yearly: end_date:{}'
                        .format(self.tenant,
                                statistics_end_date.to_iso8601_string()))

            # Worksheet for Participants by Year
            participant_worksheet = self.create_participants_worksheet(workbook, year)
            participants = statistics.participant_details()
            for row, participant in enumerate(participants, 1):
                participation_date = pendulum.instance(participant['action_date'])
                participant_worksheet.write(row, 0, participant['email'])
                participant_worksheet.write_datetime(row, 1, participation_date)
                participant_worksheet.write(row, 2, participation_date.year)
                participant_worksheet.write(row, 3, participation_date.week_of_year)

    def generate_worksheet(self, workbook, stats_type):
        formatters = self.setup_workbook_formatters(workbook)

        if stats_type == 'aggregated':
            write = self.write_total_stats
            create_worksheet = self.create_totals_worksheet
        elif stats_type == 'location_segmentation':
            write = self.write_location_segmentation_stats
            create_worksheet = self.create_location_segmentation_worksheet
        elif stats_type == 'theme_segmentation':
            write = self.write_theme_segmentation_stats
            create_worksheet = self.create_theme_segmentation_worksheet

        for year in range(self.start_date.year, self.end_date.year + 1):
            statistics_start_date = pendulum.create(year, 1, 1, 0, 0, 0)
            statistics_end_date = pendulum.create(year, 12, 31, 23, 59, 59)

            # Generate data by year
            logger.info('tenant:{} Yearly ({}): end_date:{}'
                        .format(self.tenant,
                                stats_type,
                                statistics_end_date.to_iso8601_string()))

            # Worksheet for Totals by Year
            worksheet = create_worksheet(workbook, year)

            # Add label
            row = 1
            worksheet.write(row, 0, 'By Year', formatters['metrics_header'])

            row += 1
            write(worksheet=worksheet,
                  row=row,
                  statistic_type='yearly',
                  start_date=statistics_start_date,
                  end_date=statistics_end_date)

            # Generate data by month
            row += 1
            worksheet.write(row, 0, 'By Month', formatters['metrics_header'])

            row += 1
            self.monthly_statistics_row_start = row
            for month in range(1, 13):
                statistics_end_date = pendulum.create(year, month, 1).end_of('month')

                # Stop if the end date is in the next month from current date
                if statistics_end_date < pendulum.now().add(months=1):
                    logger.info('tenant:{} Monthly ({}): end_date:{}'
                                .format(self.tenant, stats_type, statistics_end_date.to_iso8601_string())
                                )
                    write(worksheet=worksheet,
                          row=row,
                          statistic_type='monthly',
                          start_date=statistics_start_date,
                          end_date=statistics_end_date)
                    row += 1
                    self.monthly_statistics_row_end = row

            # Generate data by week
            worksheet.write(row, 0, 'By Week', formatters['metrics_header'])

            time_period = pendulum.period(statistics_start_date, pendulum.create(year, 12, 31))
            row += 1
            self.weekly_statistics_row_start = row
            for period in time_period.range('weeks'):

                # Curtail the last week of the year to end with the end of the year
                # E.g. The end day of the last week of the year could lie in the next year, in this case we just
                # use the last day of the year as the end day of the week
                statistics_end_date = period.end_of('week') \
                    if period.end_of('week') < statistics_start_date.end_of('year') \
                    else statistics_start_date.end_of('year')

                if statistics_end_date <= pendulum.now().add(weeks=1):
                    logger.info(
                        'tenant:{} Weekly ({}): end_date:{}'
                        .format(self.tenant,
                                stats_type,
                                statistics_end_date.to_iso8601_string()))
                    write(worksheet=worksheet,
                          row=row,
                          statistic_type='weekly',
                          start_date=statistics_start_date,
                          end_date=statistics_end_date)

                    row += 1
                    self.weekly_statistics_row_end = row - 1

        if stats_type == 'aggregated':
            self.create_monthly_charts(workbook, self.charts)
