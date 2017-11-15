import xlsxwriter
import calendar
import datetime
import StringIO

from django.db.models.aggregates import Count, Sum

from bluebottle.analytics.models import ProjectRawReport, TaskRawReport, TaskMemberRawReport
from bluebottle.geo.models import Location


class MetricsReport(object):

    row_lookup = {
        'project': 0,
        'task': 1,
        'taskmembers': 2,
        'taskmember_hours': 3
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

    def get_project_data(self, year=None, group=('year', )):
        return ProjectRawReport.done_objects.values(*group).annotate(value=Count('type_id', distinct=True))

    def get_task_data(self, year=None, group=('year', )):
        return TaskRawReport.objects.values(*group).\
            filter(year=year).\
            annotate(value=Count('type_id', distinct=True))

    def get_taskmember_data(self, year=None, group=('year', )):
        return TaskMemberRawReport.objects.values(*group).\
            filter(year=year).\
            annotate(value=Count('type_id', distinct=True))

    def get_taskmember_hours_data(self, year=None, group=('year', )):
        return TaskMemberRawReport.objects.values(*group).\
            filter(year=year).\
            annotate(value=Sum('value'))

    def get_data(self, year=None, group=('year', )):

        return [
            self.get_project_data(year, group),
            self.get_task_data(year, group),
            self.get_taskmember_data(year, group),
            self.get_taskmember_hours_data(year, group),
        ]

    def add_year_totals_sheet(self, year):
        border_bottom = self.formats['border']
        format_dark = self.formats['dark']
        format_grey = self.formats['light']

        ws = self.workbook.add_worksheet('Totals {}'.format(year))
        ws.merge_range(0, 0, 0, 7, 'Period', format_dark)
        ws.write(1, 0, 'Duration', format_grey)
        ws.write(1, 1, 'Year', format_grey)
        ws.write(1, 2, 'Quarter', format_grey)
        ws.write(1, 3, 'Month', format_grey)
        ws.write(1, 4, 'Week', format_grey)
        ws.write(1, 5, 'Start date', format_grey)
        ws.write(1, 6, 'End date', format_grey)

        ws.merge_range(0, 7, 0, 10, 'Totals', format_dark)
        ws.write(1, 7, 'Projects successful', format_grey)
        ws.write(1, 8, 'Activities successful', format_grey)
        ws.write(1, 9, 'Members volunteered', format_grey)
        ws.write(1, 10, 'Hours volunteered', format_grey)

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
        for data in self.get_data(year, ('year',)):
            if len(data):
                i += 1
                ws.write(2, i + 6, data[0]['value'])

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

        quarter_data = self.get_data(year, ('year', 'quarter'))
        i = 6
        for col in quarter_data:
            i += 1
            for val in col:
                j = val['quarter'] + 2
                cell_format = None
                if val['quarter'] == 4:
                    cell_format = border_bottom
                ws.write(int(j), int(i), val['value'], cell_format)

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

        month_data = self.get_data(year, ('year', 'quarter', 'month'))
        i = 6
        for col in month_data:
            i += 1
            for val in col:
                j = val['month'] + 6
                cell_format = None
                if val['month'] == 12:
                    cell_format = border_bottom
                ws.write(int(j), int(i), val['value'], cell_format)

        # Location headers
        l = 0
        for loc in self.locations:
            l += 1
            ws.merge_range(0, 7 + l * 4, 0, 10 + l * 4, loc['name'], format_dark)
            ws.write(1, l * 4 + 7, 'Projects successful', format_grey)
            ws.write(1, l * 4 + 8, 'Activities successful', format_grey)
            ws.write(1, l * 4 + 9, 'Members volunteered', format_grey)
            ws.write(1, l * 4 + 10, 'Hours volunteered', format_grey)
            for c in range(7, 11):
                ws.write(2, l * 4 + c, '', border_bottom)
                ws.write(6, l * 4 + c, '', border_bottom)
                ws.write(18, l * 4 + c, '', border_bottom)

        # Location year data
        t = 0
        for data in self.get_data(year, ('location', 'year',)):
            t += 1
            for val in data:
                if val['location']:
                    i = self.location_index[val['location']] * 4 + 6 + t
                    ws.write(2, i, val['value'], border_bottom)

        # Location quarter data
        t = 0
        for data in self.get_data(year, ('location', 'year', 'quarter')):
            t += 1
            for val in data:
                if val['location']:
                    i = self.location_index[val['location']] * 4 + 6 + t
                    j = val['quarter'] + 2
                    ws.write(int(j), int(i), val['value'], border_bottom if val['quarter'] == 4 else None)

        # Location month data
        t = 0
        for data in self.get_data(year, ('location', 'year', 'quarter', 'month')):
            t += 1
            for val in data:
                if val['location']:
                    i = self.location_index[val['location']] * 4 + 6 + t
                    j = val['month'] + 6
                    ws.write(int(j), int(i), val['value'], border_bottom if val['month'] == 12 else None)

        ws.freeze_panes(1, 7)

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

    def to_output(self):
        output = StringIO.StringIO()
        self.workbook = xlsxwriter.Workbook(output, {
            'in_memory': True,
            'default_date_format': 'dd/mm/yy',
            'remove_timezone': True
        })
        self.define_styles()
        for year in [2017, 2016]:
            self.add_year_totals_sheet(year)
        self.workbook.close()
        return output
