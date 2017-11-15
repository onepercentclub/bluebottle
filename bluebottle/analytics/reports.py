import xlsxwriter
import calendar
import datetime
import StringIO

from django.db.models.aggregates import Count, Sum

from bluebottle.analytics.models import ProjectRawReport, TaskRawReport, TaskMemberRawReport


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

    def get_project_data(self, period='year', year=None):
        if period == 'year':
            return ProjectRawReport.done_objects.values('year').\
                filter(year=year).\
                annotate(value=Count('type_id', distinct=True))
        if period == 'quarter':
            return ProjectRawReport.done_objects.values('year', 'quarter').\
                filter(year=year).\
                annotate(value=Count('type_id', distinct=True))
        if period == 'month':
            return ProjectRawReport.done_objects.values('year', 'quarter', 'month').\
                filter(year=year).\
                annotate(value=Count('type_id', distinct=True))
        if period == 'week':
            return ProjectRawReport.done_objects.values('year', 'quarter', 'month', 'week').\
                filter(year=year).\
                annotate(value=Count('type_id', distinct=True))

    def get_task_data(self, period='year', year=None):
        if period == 'year':
            return TaskRawReport.objects.values('year').\
                filter(year=year).\
                annotate(value=Count('type_id', distinct=True))
        if period == 'quarter':
            return TaskRawReport.objects.values('year', 'quarter').\
                filter(year=year).\
                annotate(value=Count('type_id', distinct=True))
        if period == 'month':
            return TaskRawReport.objects.values('year', 'quarter', 'month').\
                filter(year=year).\
                annotate(value=Count('type_id', distinct=True))
        if period == 'week':
            return TaskRawReport.objects.values('year', 'quarter', 'month', 'week').\
                filter(year=year).\
                annotate(value=Count('type_id', distinct=True))

    def get_taskmember_data(self, period='year', year=None):
        if period == 'year':
            return TaskMemberRawReport.objects.values('year').\
                filter(year=year).\
                annotate(value=Count('type_id', distinct=True))
        if period == 'quarter':
            return TaskMemberRawReport.objects.values('year', 'quarter').\
                filter(year=year).\
                annotate(value=Count('type_id', distinct=True))
        if period == 'month':
            return TaskMemberRawReport.objects.values('year', 'quarter', 'month').\
                filter(year=year).\
                annotate(value=Count('type_id', distinct=True))
        if period == 'week':
            return TaskMemberRawReport.objects.values('year', 'quarter', 'month', 'week').\
                filter(year=year).\
                annotate(value=Count('type_id', distinct=True))

    def get_taskmember_hours_data(self, period='year', year=None):
        if period == 'year':
            return TaskMemberRawReport.objects.values('year').\
                filter(year=year).\
                annotate(value=Sum('value'))
        if period == 'quarter':
            return TaskMemberRawReport.objects.values('year', 'quarter').\
                filter(year=year).\
                annotate(value=Sum('value'))
        if period == 'month':
            return TaskMemberRawReport.objects.values('year', 'quarter', 'month').\
                filter(year=year).\
                annotate(value=Sum('value'))
        if period == 'week':
            return TaskMemberRawReport.objects.values('year', 'quarter', 'month', 'week').\
                filter(year=year).\
                annotate(value=Sum('value'))

    def add_year_totals(self, year):
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
        year_data = self.get_project_data('year', year)
        if len(year_data):
            ws.write(2, 7, year_data[0]['value'])
        else:
            pass
        year_data = self.get_task_data('year', year)
        if len(year_data):
            ws.write(2, 8, year_data[0]['value'])
        else:
            pass
        year_data = self.get_taskmember_data('year', year)
        if len(year_data):
            ws.write(2, 9, year_data[0]['value'])
        else:
            pass
        year_data = self.get_taskmember_hours_data('year', year)
        if len(year_data):
            ws.write(2, 10, year_data[0]['value'])
        else:
            pass

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

        quarter_data = self.get_project_data('quarter', year)
        for val in quarter_data:
            i = 7
            j = val['quarter'] + 2
            cell_format = None
            if val['quarter'] == 4:
                cell_format = border_bottom
            ws.write(int(j), int(i), val['value'], cell_format)

        quarter_data = self.get_task_data('quarter', year)
        for val in quarter_data:
            i = 8
            j = val['quarter'] + 2
            cell_format = None
            if val['quarter'] == 4:
                cell_format = border_bottom
            ws.write(int(j), int(i), val['value'], cell_format)

        quarter_data = self.get_taskmember_data('quarter', year)
        for val in quarter_data:
            i = 9
            j = val['quarter'] + 2
            cell_format = None
            if val['quarter'] == 4:
                cell_format = border_bottom
            ws.write(int(j), int(i), val['value'], cell_format)

        quarter_data = self.get_taskmember_hours_data('quarter', year)
        for val in quarter_data:
            i = 10
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

        month_data = self.get_project_data('month', year)
        for val in month_data:
            i = 7
            j = val['month'] + 6
            cell_format = None
            if val['month'] == 12:
                cell_format = border_bottom
            ws.write(int(j), int(i), val['value'], cell_format)

        month_data = self.get_task_data('month', year)
        for val in month_data:
            i = 8
            j = val['month'] + 6
            cell_format = None
            if val['month'] == 12:
                cell_format = border_bottom
            ws.write(int(j), int(i), val['value'], cell_format)

        month_data = self.get_taskmember_data('month', year)
        for val in month_data:
            i = 9
            j = val['month'] + 6
            cell_format = None
            if val['month'] == 12:
                cell_format = border_bottom
            ws.write(int(j), int(i), val['value'], cell_format)

        month_data = self.get_taskmember_hours_data('month', year)
        for val in month_data:
            i = 10
            j = val['month'] + 6
            cell_format = None
            if val['month'] == 12:
                cell_format = border_bottom
            ws.write(int(j), int(i), val['value'], cell_format)

    def define_styles(self):
        self.formats['dark'] = self.workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#555555',
            'align': 'center'
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
        for year in [2017, 2016, 2015]:
            self.add_year_totals(year)
        self.workbook.close()
        return output
