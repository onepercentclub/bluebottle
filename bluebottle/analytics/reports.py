import xlsxwriter
import calendar
import datetime
import StringIO

from bluebottle.analytics.models import get_report_model, get_raw_report_model
from bluebottle.geo.models import Location


class MetricsReport(object):

    type_index = {
        'project': 0,
        'task': 1,
        'taskmembers': 2,
        'taskvolunteers': 3,
        'taskmember_hours': 4
    }

    formats = {}

    def __init__(self):
        pass

    @property
    def locations(self):
        return Location.objects.order_by('name').values('id', 'name')

    @property
    def location_index(self):
        index = {}
        i = 0
        for loc in self.locations:
            i += 1
            index[loc['name']] = i
        return index

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
        self.formats['border'] = self.workbook.add_format({'bottom': 1})
        self.formats['right_border'] = self.workbook.add_format({'right': 1})
        self.formats['top'] = self.workbook.add_format({'valign': 'top'})

    def get_year_data(self, year, location=False, cumulative=False):
        if location:
            ReportModel = get_report_model('v_year_report')
        else:
            ReportModel = get_report_model('v_year_totals_report')
        return ReportModel.objects.filter(year=year)

    def get_quarter_data(self, year, location=False, cumulative=False):
        if location:
            ReportModel = get_report_model('v_quarter_report')
        else:
            ReportModel = get_report_model('v_quarter_totals_report')
        return ReportModel.objects.filter(year=year).order_by('quarter', 'type')

    def get_month_data(self, year, location=False, cumulative=False):
        if location:
            ReportModel = get_report_model('v_month_report')
        else:
            ReportModel = get_report_model('v_month_totals_report')
        return ReportModel.objects.filter(year=year).order_by('month', 'type')

    def add_project_sheet(self):
        right_border = self.formats['right_border']
        dark = self.formats['dark']
        light = self.formats['light']
        ws = self.workbook.add_worksheet('All projects successful')
        ws.merge_range(0, 0, 0, 4, 'Project', dark)
        ws.write(1, 0, 'Project id', light)
        ws.write(1, 1, 'Project title', light)
        ws.write(1, 2, 'Project location', light)
        ws.write(1, 3, 'Date last status log change to \'Project Realized\'', light)
        ws.write(1, 4, 'Status', light)
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
            ws.write(r, 0, data.type_id)
            ws.write(r, 1, data.description)
            ws.write(r, 2, data.location)
            ws.write(r, 3, data.event_timestamp)
            ws.write(r, 4, data.status, right_border)
            ws.write(r, 5, data.year)
            ws.write(r, 6, data.quarter)
            ws.write(r, 7, data.month)
            ws.write(r, 8, data.week)

    def add_task_sheet(self):
        right_border = self.formats['right_border']
        dark = self.formats['dark']
        light = self.formats['light']
        ws = self.workbook.add_worksheet('All activities successful')
        ws.merge_range(0, 0, 0, 3, 'Activity', dark)
        ws.write(1, 0, 'Activity id', light)
        ws.write(1, 1, 'Activity title', light)
        ws.write(1, 2, 'Activity deadline', light)
        ws.write(1, 3, 'Activity status', light)
        ws.merge_range(0, 4, 0, 6, 'Project', dark)
        ws.write(1, 4, 'Project id', light)
        ws.write(1, 5, 'Project title', light)
        ws.write(1, 6, 'Project location', light)
        ws.merge_range(0, 7, 0, 10, 'Period', dark)
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
            ws.write(r, 0, data.type_id)
            ws.write(r, 1, data.description)
            ws.write(r, 2, data.timestamp)
            ws.write(r, 3, data.status, right_border)
            ws.write(r, 4, data.parent_id)
            ws.write(r, 5, data.parent_description)
            ws.write(r, 6, data.location)
            ws.write(r, 7, data.year)
            ws.write(r, 8, data.quarter)
            ws.write(r, 9, data.month)
            ws.write(r, 10, data.week)

    def add_taskmember_sheet(self):
        right_border = self.formats['right_border']
        dark = self.formats['dark']
        light = self.formats['light']
        ws = self.workbook.add_worksheet('All members & hours volunteered')
        ws.merge_range(0, 0, 0, 3, 'Activity member', dark)
        ws.write(1, 0, 'Id', light)
        ws.write(1, 1, 'Status', light)
        ws.write(1, 2, 'Hours pledged', light)
        ws.write(1, 3, 'Hours realized', light)
        ws.merge_range(0, 4, 0, 6, 'Related Member', dark)
        ws.write(1, 4, 'Id', light)
        ws.write(1, 5, 'Remote id', light)
        ws.write(1, 6, 'Email', light)
        ws.merge_range(0, 7, 0, 9, 'Related Activity', dark)
        ws.write(1, 7, 'Id', light)
        ws.write(1, 8, 'Title', light)
        ws.write(1, 9, 'Deadline', light)
        ws.merge_range(0, 10, 0, 12, 'Related Project', dark)
        ws.write(1, 10, 'Id', light)
        ws.write(1, 11, 'Title', light)
        ws.write(1, 12, 'Location', light)
        ws.merge_range(0, 13, 0, 16, 'Related Activity', dark)
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
            ws.write(r, 0, data.type_id)
            ws.write(r, 1, data.status)
            ws.write(r, 2, data.pledged)
            ws.write(r, 3, data.value, right_border)

            ws.write(r, 4, data.user_id)
            ws.write(r, 5, data.user_remote_id)
            ws.write(r, 6, data.user_email)

            ws.write(r, 7, data.parent_id)
            ws.write(r, 8, data.parent_description)
            ws.write(r, 9, data.timestamp)

            ws.write(r, 10, data.grand_parent_id)
            ws.write(r, 11, data.grand_parent_description)
            ws.write(r, 12, data.location)

            ws.write(r, 13, data.year)
            ws.write(r, 14, data.quarter)
            ws.write(r, 15, data.month)
            ws.write(r, 16, data.week)

    def add_year_totals_sheet(self, year):
        border_bottom = self.formats['border']
        dark = self.formats['dark']
        light = self.formats['light']

        ws = self.workbook.add_worksheet('Totals {}'.format(year))
        ws.merge_range(0, 0, 0, 7, 'Period', dark)
        ws.write(1, 0, 'Duration', light)
        ws.write(1, 1, 'Year', light)
        ws.write(1, 2, 'Quarter', light)
        ws.write(1, 3, 'Month', light)
        ws.write(1, 4, 'Week', light)
        ws.write(1, 5, 'Start date', light)
        ws.write(1, 6, 'End date', light)

        ws.merge_range(0, 7, 0, 11, 'Totals', dark)
        ws.write(1, 7, 'Projects successful', light)
        ws.write(1, 8, 'Activities successful', light)
        ws.write(1, 9, 'Activity members', light)
        ws.write(1, 10, 'Members volunteered', light)
        ws.write(1, 11, 'Hours volunteered', light)

        # Rows for year
        start = datetime.date(year, 1, 1)
        end = datetime.date(year, 12, 31)
        ws.write(2, 0, 'Year', border_bottom)
        ws.write(2, 1, year, border_bottom)
        ws.write(2, 2, '', border_bottom)
        ws.write(2, 3, '', border_bottom)
        ws.write(2, 4, '', border_bottom)
        ws.write_datetime(2, 5, date=start)
        ws.write_datetime(2, 6, date=end)

        # Values for year
        i = 0
        for data in self.get_year_data(year):
            i += 1
            ws.write(2, i + 6, data.value)

        # Rows for quarter
        for q in range(1, 5):
            start = datetime.date(year, q * 3 - 2, 1)
            end = datetime.date(year, q * 3, calendar.monthrange(year, q * 3)[1])
            cell_format = None
            if q == 4:
                cell_format = border_bottom
            ws.write(2 + q, 0, 'Quarter', cell_format)
            ws.write(2 + q, 1, year, cell_format)
            ws.write(2 + q, 2, q, cell_format)
            ws.write(2 + q, 3, '', cell_format)
            ws.write(2 + q, 4, '', cell_format)
            ws.write_datetime(2 + q, 5, start)
            ws.write_datetime(2 + q, 6, end)

        quarter_data = self.get_quarter_data(year)
        for data in quarter_data:
            j = data.quarter + 2
            i = self.type_index[data.type] + 7
            cell_format = None
            if data.quarter == 4:
                cell_format = border_bottom
            ws.write(int(j), int(i), data.value, cell_format)

        # Rows for months
        for m in range(1, 13):
            start = datetime.date(year, m, 1)
            end = datetime.date(year, m, calendar.monthrange(year, m)[1])
            cell_format = None
            if m == 12:
                cell_format = border_bottom
            ws.write(6 + m, 0, 'Month', cell_format)
            ws.write(6 + m, 1, year, cell_format)
            ws.write(6 + m, 2, '', cell_format)
            ws.write(6 + m, 3, start.strftime('%B'), cell_format)
            ws.write(6 + m, 4, '', cell_format)
            ws.write(6 + m, 5, start)
            ws.write_datetime(6 + m, 6, end)

        month_data = self.get_month_data(year)
        for data in month_data:
            j = data.month + 6
            i = self.type_index[data.type] + 7
            ws.write(int(j), int(i), data.value, border_bottom if data.month == 12 else None)

        # Location headers
        lc = 0
        for loc in self.locations:
            lc += 1
            ws.merge_range(0, 7 + lc * 5, 0, 11 + lc * 5, loc['name'], dark)
            ws.write(1, lc * 5 + 7, 'Projects successful', light)
            ws.write(1, lc * 5 + 8, 'Activities successful', light)
            ws.write(1, lc * 5 + 9, 'Activity members', light)
            ws.write(1, lc * 5 + 10, 'Members volunteered', light)
            ws.write(1, lc * 5 + 11, 'Hours volunteered', light)
            for c in range(7, 12):
                ws.write(2, lc * 5 + c, '', border_bottom)
                ws.write(6, lc * 5 + c, '', border_bottom)
                ws.write(18, lc * 5 + c, '', border_bottom)

        # Location year data
        for data in self.get_year_data(year, location=True):
            if data.location:
                t = self.type_index[data.type]
                i = self.location_index[data.location] * 5 + 7 + t
                ws.write(2, i, data.value, border_bottom)

        # Location quarter data
        for data in self.get_quarter_data(year, location=True):
            if data.location:
                t = self.type_index[data.type]
                i = self.location_index[data.location] * 5 + 7 + t
                j = data.quarter + 2
                ws.write(int(j), int(i), data.value, border_bottom if data.quarter == 4 else None)

        # Location month data
        for data in self.get_month_data(year, location=True):
            if data.location:
                t = self.type_index[data.type]
                i = self.location_index[data.location] * 5 + 7 + t
                j = data.month + 6
                ws.write(int(j), int(i), data.value, border_bottom if data.month == 12 else None)

        ws.freeze_panes(1, 7)

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
  'Project Realized' that new date is used for determining the period in which is counted.""")

        ws.write_string(2, 0, 'Activities successful', top)
        ws.write_string(2, 1, """Total sum of tasks with status 'Realized'.

Date considered for selecting the correct <period>:
- Task - Deadline.""")

        ws.write_string(3, 0, 'Activity members volunteered', top)
        ws.write_string(3, 1, """Total sum of unique task members who realized a task (task member's
status is 'Realized') with more than 0 hours realized.

Date considered for selecting the correct <period>:
- 'Task - Deadline' of the task belonging to the task member.""")

        ws.write_string(4, 0, 'Members volunteered', top)
        ws.write_string(4, 1, """Total sum of unique members who realized a task (task member's
status is 'Realized') with more than 0 hours realized.

Date considered for selecting the correct <period>:
- 'Task - Deadline' of the task belonging to the task member.""")

        ws.write_string(5, 0, 'Hours volunteered', top)
        ws.write_string(5, 1, """Total sum of hours realized belonging to any task member who realized
a task (task member status is 'Realized').

Date considered for selecting the correct <period>:
- 'Task - Deadline' of the task belonging to the task member.""")

        ws.write_string(6, 0, 'Filter', dark)
        ws.write_string(6, 1, 'Definition', dark)

        ws.write_string(7, 0, 'Project location', top)
        ws.write_string(7, 1, """For all the metrics above we're filtering on the location of the
project that belongs to the project, tasks and task members.

Note
- Because the location for member is not populated, we are not filtering on for example the 'office location'
  of a member.""")

    def to_output(self):
        output = StringIO.StringIO()
        self.workbook = xlsxwriter.Workbook(output, {
            'in_memory': True,
            'default_date_format': 'dd/mm/yy',
            'remove_timezone': True
        })
        self.define_styles()
        self.add_definition_sheet()
        for year in [2017, 2016]:
            self.add_year_totals_sheet(year)
        self.add_project_sheet()
        self.add_task_sheet()
        self.add_taskmember_sheet()
        self.workbook.close()
        return output
