import time
import xlsxwriter
import calendar
import datetime
import StringIO
import operator
import logging

from django.db import connection
from django.utils import timezone

from bluebottle.analytics.models import get_report_model, get_raw_report_model
from bluebottle.projects.models import Project

logger = logging.getLogger(__name__)


class MetricsReport(object):

    type_index = {
        'project': 0,
        'task': 1,
        'taskmember_volunteers': 2,
        'member_volunteers': 3,
        'taskmember_hours': 4
    }

    date_format = 'dd/mm/yy'
    formats = {}

    def __init__(self):
        pass

    def locations_by_year(self, year):
        # Only fetch locations with data by using v_year_report
        ReportModel = get_report_model('v_year_report')
        locations_query = ReportModel.objects.filter(year=year).exclude(location=u'')
        locations = locations_query.values('location').order_by('location').distinct()
        location_index = {}
        i = 0
        for loc in locations:
            i += 1
            location_index[loc['location']] = i

        return locations, location_index

    def define_styles(self):
        self.formats['dark'] = self.workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#555555',
            'align': 'center',
            'right': 1,
            'border_color': '#FFFFFF'
        })
        self.formats['light'] = self.workbook.add_format({'bg_color': '#DDDDDD'})
        self.formats['light_border_right'] = self.workbook.add_format({'bg_color': '#DDDDDD', 'right': 1})
        self.formats['border_bottom'] = self.workbook.add_format({'bottom': 1})
        self.formats['border_right'] = self.workbook.add_format({'right': 1})
        self.formats['border_corner'] = self.workbook.add_format({'bottom': 1, 'right': 1})
        self.formats['border_date_bottom'] = self.workbook.add_format({'num_format': self.date_format, 'bottom': 1})
        self.formats['border_date_right'] = self.workbook.add_format({'num_format': self.date_format, 'right': 1})
        self.formats['right_border'] = self.workbook.add_format({'right': 1})
        self.formats['top'] = self.workbook.add_format({'valign': 'top', 'text_wrap': 1})

    def add_definition_sheet(self):
        ws = self.workbook.add_worksheet('Definitions')
        dark = self.formats['dark']
        top = self.formats['top']
        ws.set_column(0, 0, 40)
        ws.set_column(1, 1, 80)
        ws.write_string(0, 0, 'Metric', dark)
        ws.write_string(0, 1, 'Definition', dark)
        ws.write_string(1, 0, 'Projects successful', top)

        ws.write_string(1, 1, """Total sum of projects with status 'Project - Realized'.
Date considered for selecting the correct <period>:
- Date of project's last status log change to 'Project - Realized'

Notes
- This counts unique projects, not unique project owners.
- We do not use date fields such as 'campaign ended' or 'campaign funded'.
- When you change the project status back to running and then again back to
  'Project Realized' that new date is used for determining the period in which is counted.""", top)

        ws.write_string(2, 0, 'Activities successful', top)
        ws.write_string(2, 1, """Total sum of tasks with status 'Realized'.

Date considered for selecting the correct <period>:
- Task - Deadline.""", top)

        ws.write_string(3, 0, 'Activity members volunteered', top)
        ws.write_string(3, 1, """Total sum of task members who realized a task (task member's
status is 'Realized') with more than 0 hours realized.

Date considered for selecting the correct <period>:
- 'Task - Deadline' of the task belonging to the task member.""", top)

        ws.write_string(4, 0, 'Members volunteered', top)
        ws.write_string(4, 1, """Total sum of unique members who realized a task (task member's
status is 'Realized') with more than 0 hours realized.

Date considered for selecting the correct <period>:
- 'Task - Deadline' of the task belonging to the task member.""", top)

        ws.write_string(5, 0, 'Hours volunteered', top)
        ws.write_string(5, 1, """Total sum of hours realized belonging to any task member who realized
a task (task member status is 'Realized').

Date considered for selecting the correct <period>:
- 'Task - Deadline' of the task belonging to the task member.""", top)

        ws.write_string(6, 0, 'Filter', dark)
        ws.write_string(6, 1, 'Definition', dark)

        ws.write_string(7, 0, 'Project location', top)
        ws.write_string(7, 1, """For all the metrics above we're filtering on the location of the
project that belongs to the project, tasks and task members.

Note
- Because the location for member is not populated, we are not filtering on for example
  the 'office location' of a member.""", top)

    def get_year_data(self, year, location=False, cumulative=False):
        if cumulative:
            if location:
                ReportModel = get_report_model('v_year_cumulative_report')
            else:
                ReportModel = get_report_model('v_year_cumulative_totals_report')
        else:
            if location:
                ReportModel = get_report_model('v_year_report')
            else:
                ReportModel = get_report_model('v_year_totals_report')
        return ReportModel.objects.filter(year=year)

    def get_quarter_data(self, year, location=False, cumulative=False):
        if cumulative:
            if location:
                ReportModel = get_report_model('v_quarter_cumulative_report')
            else:
                ReportModel = get_report_model('v_quarter_cumulative_totals_report')
        else:
            if location:
                ReportModel = get_report_model('v_quarter_report')
            else:
                ReportModel = get_report_model('v_quarter_totals_report')
        return ReportModel.objects.filter(year=year).order_by('year', 'quarter', 'type')

    def get_month_data(self, year, location=False, cumulative=False):
        if cumulative:
            if location:
                ReportModel = get_report_model('v_month_cumulative_report')
            else:
                ReportModel = get_report_model('v_month_cumulative_totals_report')
        else:
            if location:
                ReportModel = get_report_model('v_month_report')
            else:
                ReportModel = get_report_model('v_month_totals_report')
        return ReportModel.objects.filter(year=year).order_by('year', 'quarter', 'month', 'type')

    def _write_standard_cell(self, worksheet, row, column, value, cell_format=None):
        if not cell_format:
            cell_format = self.workbook.add_format({})
        cell_format.set_align('left')
        worksheet.write(row, column, value, cell_format)

    def add_project_sheet(self):
        border_date_right = self.formats['border_date_right']
        dark = self.formats['dark']
        light = self.formats['light']
        light_border = self.formats['light_border_right']
        ws = self.workbook.add_worksheet('All projects successful')
        ws.merge_range(0, 0, 0, 4, 'Project', dark)
        ws.write(1, 0, 'Project id', light)
        ws.write(1, 1, 'Project title', light)
        ws.write(1, 2, 'Project location', light)
        ws.write(1, 3, 'Project status', light)
        ws.write(1, 4, 'Date last status log change to \'Project Realized\'', light_border)
        ws.merge_range(0, 5, 0, 8, 'Period', dark)
        ws.write(1, 5, 'Year', light)
        ws.write(1, 6, 'Quarter', light)
        ws.write(1, 7, 'Month', light)
        ws.write(1, 8, 'Week', light)

        ws.set_column(1, 1, 40)
        ws.set_column(2, 2, 20)
        ws.set_column(3, 3, 12)
        ws.set_column(4, 4, 20)

        ReportModel = get_raw_report_model('v_project_successful_report')
        project_data = ReportModel.objects.order_by('event_timestamp').all()
        r = 1
        for data in project_data:
            r += 1
            self._write_standard_cell(ws, r, 0, data.type_id)
            self._write_standard_cell(ws, r, 1, data.description)
            self._write_standard_cell(ws, r, 2, data.location)
            self._write_standard_cell(ws, r, 3, data.status_friendly)
            self._write_standard_cell(ws, r, 4, data.event_timestamp, border_date_right)
            self._write_standard_cell(ws, r, 5, data.year)
            self._write_standard_cell(ws, r, 6, data.quarter)
            self._write_standard_cell(ws, r, 7, data.month)
            self._write_standard_cell(ws, r, 8, data.week)

    def add_task_sheet(self):
        right_border = self.formats['right_border']
        border_date_right = self.formats['border_date_right']
        dark = self.formats['dark']
        light = self.formats['light']
        light_border = self.formats['light_border_right']
        ws = self.workbook.add_worksheet('All activities successful')
        ws.merge_range(0, 0, 0, 3, 'Activity', dark)
        ws.write(1, 0, 'Activity id', light)
        ws.write(1, 1, 'Activity title', light)
        ws.write(1, 2, 'Activity status', light)
        ws.write(1, 3, 'Activity deadline', light_border)
        ws.merge_range(0, 4, 0, 6, 'Related project', dark)
        ws.write(1, 4, 'Project id', light)
        ws.write(1, 5, 'Project title', light)
        ws.write(1, 6, 'Project location', light_border)
        ws.merge_range(0, 7, 0, 10, 'Related period', dark)
        ws.write(1, 7, 'Year', light)
        ws.write(1, 8, 'Quarter', light)
        ws.write(1, 9, 'Month', light)
        ws.write(1, 10, 'Week', light)

        ws.set_column(1, 1, 40)
        ws.set_column(2, 2, 12)
        ws.set_column(5, 5, 40)
        ws.set_column(6, 6, 20)

        ReportModel = get_raw_report_model('v_task_successful_report')
        project_data = ReportModel.objects.order_by('timestamp').all()
        r = 1
        for data in project_data:
            r += 1
            self._write_standard_cell(ws, r, 0, data.type_id)
            self._write_standard_cell(ws, r, 1, data.description)
            self._write_standard_cell(ws, r, 2, data.status_friendly)
            self._write_standard_cell(ws, r, 3, data.timestamp, border_date_right)
            self._write_standard_cell(ws, r, 4, data.parent_id)
            self._write_standard_cell(ws, r, 5, data.parent_description)
            self._write_standard_cell(ws, r, 6, data.location, right_border)
            self._write_standard_cell(ws, r, 7, data.year)
            self._write_standard_cell(ws, r, 8, data.quarter)
            self._write_standard_cell(ws, r, 9, data.month)
            self._write_standard_cell(ws, r, 10, data.week)

    def add_taskmember_sheet(self):
        right_border = self.formats['right_border']
        border_date_right = self.formats['border_date_right']
        dark = self.formats['dark']
        light = self.formats['light']
        light_border = self.formats['light_border_right']
        ws = self.workbook.add_worksheet('All members & hours volunteered')
        ws.merge_range(0, 0, 0, 3, 'Activity member', dark)
        ws.write(1, 0, 'Activity member id', light)
        ws.write(1, 1, 'Activity member status', light)
        ws.write(1, 2, 'Hours pledged', light)
        ws.write(1, 3, 'Hours realized', light_border)
        ws.merge_range(0, 4, 0, 6, 'Related Member', dark)
        ws.write(1, 4, 'Member id', light)
        ws.write(1, 5, 'Employee id', light)
        ws.write(1, 6, 'Email', light_border)
        ws.merge_range(0, 7, 0, 9, 'Related Activity', dark)
        ws.write(1, 7, 'Activity id', light)
        ws.write(1, 8, 'Activity title', light)
        ws.write(1, 9, 'Deadline', light_border)
        ws.merge_range(0, 10, 0, 12, 'Related Project', dark)
        ws.write(1, 10, 'Project id', light)
        ws.write(1, 11, 'Project title', light)
        ws.write(1, 12, 'Location', light_border)
        ws.merge_range(0, 13, 0, 16, 'Related Period', dark)
        ws.write(1, 13, 'Year', light)
        ws.write(1, 14, 'Quarter', light)
        ws.write(1, 15, 'Month', light)
        ws.write(1, 16, 'Week', light)

        ws.set_column(6, 6, 20)
        ws.set_column(8, 8, 40)
        ws.set_column(11, 11, 40)
        ws.set_column(12, 12, 20)

        ReportModel = get_raw_report_model('v_taskmember_successful_report')
        project_data = ReportModel.objects.order_by('timestamp').all()
        r = 1
        for data in project_data:
            r += 1
            self._write_standard_cell(ws, r, 0, data.type_id)
            self._write_standard_cell(ws, r, 1, data.status_friendly)
            self._write_standard_cell(ws, r, 2, data.value_alt)
            self._write_standard_cell(ws, r, 3, data.value, right_border)
            self._write_standard_cell(ws, r, 4, data.user_id)
            self._write_standard_cell(ws, r, 5, data.user_remote_id)
            self._write_standard_cell(ws, r, 6, data.user_email, right_border)
            self._write_standard_cell(ws, r, 7, data.parent_id)
            self._write_standard_cell(ws, r, 8, data.parent_description)
            self._write_standard_cell(ws, r, 9, data.timestamp, border_date_right)
            self._write_standard_cell(ws, r, 10, data.grand_parent_id)
            self._write_standard_cell(ws, r, 11, data.grand_parent_description)
            self._write_standard_cell(ws, r, 12, data.location, right_border)
            self._write_standard_cell(ws, r, 13, data.year)
            self._write_standard_cell(ws, r, 14, data.quarter)
            self._write_standard_cell(ws, r, 15, data.month)
            self._write_standard_cell(ws, r, 16, data.week)

    def add_year_totals_sheet(self, year, cumulative=False):

        last_type = max(self.type_index.iteritems(), key=operator.itemgetter(1))[0]
        border_bottom = self.formats['border_bottom']
        border_right = self.formats['border_right']
        border_bottom_right = self.formats['border_corner']
        date_border_bottom = self.formats['border_date_bottom']
        dark = self.formats['dark']
        light = self.formats['light']
        light_border = self.formats['light_border_right']
        if cumulative:
            ws = self.workbook.add_worksheet('Aggregated Totals {}'.format(year))
        else:
            ws = self.workbook.add_worksheet('Totals {}'.format(year))
        # Number of columns in period section
        period_width = 6
        # number of types
        num_types = len(self.type_index.keys())

        locations, location_index = self.locations_by_year(year)

        # Set border for period section
        def _period_border(right_check=False):
            if right_check:
                cell_format = border_bottom
                cell_date_format = date_border_bottom
            else:
                cell_format = self.workbook.add_format({})
                cell_date_format = self.workbook.add_format({'num_format': self.date_format})

            cell_format.set_align('left')
            cell_date_format.set_align('left')

            return cell_format, cell_date_format

        # Set location section borders
        def _location_borders(l_index=0):
            # Add bottom borders for year, quarter and month sections
            for c in range(7, 12):
                ws.write(2, l_index * 5 + c, '', border_bottom)
                ws.write(6, l_index * 5 + c, '', border_bottom)
                ws.write(18, l_index * 5 + c, '', border_bottom)

            # Add right border for location block
            for c in range(2, 19):
                if c in [2, 6, 18]:
                    cell_border = border_bottom_right
                else:
                    cell_border = border_right
                ws.write(c, l_index * 5 + period_width + num_types, '', cell_border)

        # Set cell borders within location sections. right_check is true if the
        # cell is at the right most side of the section.
        def _cell_border(data, right_check, is_date=False):
            if data.type == last_type and right_check:
                cell_border = border_bottom_right
            elif data.type == last_type:
                cell_border = border_right
            elif right_check:
                cell_border = border_bottom if not is_date else date_border_bottom
            else:
                cell_border = self.workbook.add_format({})

            cell_border.set_align('left')
            return cell_border

        def _quarter_write(i, j, data, last_row=False):
            cell_border = _cell_border(data, last_row)
            ws.write(int(j), int(i), data.value, cell_border)

        def _month_write(i, j, data, last_row):
            cell_border = _cell_border(data, last_row)
            ws.write(int(j), int(i), data.value, cell_border)

        # Write Period section
        ws.merge_range(0, 0, 0, period_width, 'Period', dark)
        ws.write(1, 0, 'Duration', light)
        ws.write(1, 1, 'Year', light)
        ws.write(1, 2, 'Quarter', light)
        ws.write(1, 3, 'Month', light)
        ws.write(1, 4, 'Week', light)
        ws.write(1, 5, 'Start date', light)
        ws.write(1, 6, 'End date', light)

        # Rows for year
        border_bottom.set_align('left')
        start = datetime.date(year, 1, 1)
        end = datetime.date(year, 12, 31)
        ws.write(2, 0, 'Year', border_bottom)
        ws.write(2, 1, year, border_bottom)
        ws.write(2, 2, '', border_bottom)
        ws.write(2, 3, '', border_bottom)
        ws.write(2, 4, '', border_bottom)
        ws.write_datetime(2, 5, date=start, cell_format=date_border_bottom)
        ws.write_datetime(2, 6, date=end, cell_format=date_border_bottom)

        _location_borders()

        """ Begin Period Section """

        # Rows for quarter
        for q in range(1, 5):
            q_start = start if cumulative else datetime.date(year, q * 3 - 2, 1)
            end = datetime.date(year, q * 3, calendar.monthrange(year, q * 3)[1])

            cell_format, cell_date_format = _period_border(q == 4)
            ws.write(2 + q, 0, 'Quarter', cell_format)
            ws.write(2 + q, 1, year, cell_format)
            ws.write(2 + q, 2, q, cell_format)
            ws.write(2 + q, 3, '', cell_format)
            ws.write(2 + q, 4, '', cell_format)
            ws.write_datetime(2 + q, 5, q_start, cell_format=cell_date_format)
            ws.write_datetime(2 + q, 6, end, cell_format=cell_date_format)

        # Total rows for months
        for m in range(1, 13):
            m_start = start if cumulative else datetime.date(year, m, 1)
            m_period = datetime.date(year, m, 1)
            end = datetime.date(year, m, calendar.monthrange(year, m)[1])

            cell_format, cell_date_format = _period_border(m == 12)
            ws.write(6 + m, 0, 'Month', cell_format)
            ws.write(6 + m, 1, year, cell_format)
            ws.write(6 + m, 2, '', cell_format)
            ws.write(6 + m, 3, m_period.strftime('%B'), cell_format)
            ws.write(6 + m, 4, '', cell_format)
            ws.write_datetime(6 + m, 5, m_start, cell_format=cell_date_format)
            ws.write_datetime(6 + m, 6, end, cell_format=cell_date_format)

        """ End Period Section """

        """ Begin Totals Section """

        # Write totals section
        ws.merge_range(0, period_width + 1, 0, period_width + num_types, 'Totals', dark)
        ws.write(1, 7, 'Projects successful', light)
        ws.write(1, 8, 'Activities successful', light)
        ws.write(1, 9, 'Activity members volunteered', light)
        ws.write(1, 10, 'Members volunteered', light)
        ws.write(1, 11, 'Hours volunteered', light_border)

        # Totals rows for year
        for data in self.get_year_data(year, cumulative=cumulative):
            i = self.type_index[data.type] + 7

            cell_border = _cell_border(data, True)
            ws.write(2, i, data.value, cell_border)

        # Total rows for quarters
        quarter_data = self.get_quarter_data(year, cumulative=cumulative)
        for data in quarter_data:
            j = data.quarter + 2
            i = self.type_index[data.type] + 7

            _quarter_write(i, j, data, data.quarter == 4)

            # FIXME: filling forward to ensure no gaps if subsequent quarters have no data
            if cumulative:
                for quarter in range(int(data.quarter) + 1, 5):
                    j = quarter + 2
                    _quarter_write(i, j, data, quarter == 4)

        # Total rows for months
        month_data = self.get_month_data(year, cumulative=cumulative)
        for data in month_data:
            j = data.month + 6
            i = self.type_index[data.type] + 7

            _month_write(i, j, data, data.month == 12)

            # FIXME: filling forward to ensure no gaps if subsequent months have no data
            if cumulative:
                for month in range(int(data.month) + 1, 13):
                    j = month + 6
                    _month_write(i, j, data, month == 12)

        """ End Totals Section """

        """ Begin Location Sections """

        # Location headers
        lc = 0
        for loc in locations:
            lc += 1
            ws.merge_range(0, 7 + lc * 5, 0, 11 + lc * 5, loc['location'], dark)
            ws.write(1, lc * 5 + 7, 'Projects successful', light)
            ws.write(1, lc * 5 + 8, 'Activities successful', light)
            ws.write(1, lc * 5 + 9, 'Activity members volunteered', light)
            ws.write(1, lc * 5 + 10, 'Members volunteered', light)
            ws.write(1, lc * 5 + 11, 'Hours volunteered', light_border)

            _location_borders(lc)

        # Location year data
        for data in self.get_year_data(year, location=True, cumulative=cumulative):
            if data.location:
                t = self.type_index[data.type]
                i = location_index[data.location] * 5 + 7 + t

                cell_border = _cell_border(data, True)
                ws.write(2, i, data.value, cell_border)

        # Location quarter data
        for data in self.get_quarter_data(year, location=True, cumulative=cumulative):
            if data.location:
                t = self.type_index[data.type]
                i = location_index[data.location] * 5 + 7 + t
                j = data.quarter + 2

                _quarter_write(i, j, data, data.quarter == 4)

                # FIXME: filling forward to ensure no gaps if subsequent quarters have no data
                if cumulative:
                    for quarter in range(int(data.quarter) + 1, 5):
                        j = quarter + 2
                        _quarter_write(i, j, data, quarter == 4)

        # Location month data
        for data in self.get_month_data(year, location=True, cumulative=cumulative):
            if data.location:
                t = self.type_index[data.type]
                i = location_index[data.location] * 5 + 7 + t
                j = data.month + 6

                _month_write(i, j, data, data.month == 12)

                # FIXME: filling forward to ensure no gaps if subsequent months have no data
                if cumulative:
                    for month in range(int(data.month) + 1, 13):
                        j = month + 6
                        _month_write(i, j, data, month == 12)

        """ End Location Sections """

        ws.freeze_panes(1, 7)

    def to_output(self):
        start_time = time.time()

        output = StringIO.StringIO()
        self.workbook = xlsxwriter.Workbook(output, {
            'in_memory': True,
            'default_date_format': 'dd/mm/yy',
            'remove_timezone': True
        })
        self.define_styles()
        self.add_definition_sheet()

        genesis = Project.objects.order_by('created')[0].created.year
        year = timezone.now().year

        while year >= genesis:
            self.add_year_totals_sheet(year)
            self.add_year_totals_sheet(year, cumulative=True)
            year -= 1
        self.add_project_sheet()
        self.add_task_sheet()
        self.add_taskmember_sheet()
        self.workbook.close()

        tenant = connection.tenant.client_name
        logger.info("Report for %s generated in %s secs", tenant, time.time() - start_time,
                    exc_info=1)

        return output
