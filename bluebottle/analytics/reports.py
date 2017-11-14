import pendulum
import xlsxwriter
import calendar
import datetime
import StringIO

from bluebottle.analytics.models import get_report_model


class MetricsReport(object):

    row_lookup = {
        'project': 0,
        'task': 1,
        'taskmembers': 2,
        'taskmember_hours': 3
    }

    def __init__(self):
        pass

    def get_file_name(self):
        now = pendulum.now()
        file_name = 'metrics_report_generated_{}_{}.xlsx'.format(
            now.to_date_string(),
            now.int_timestamp
        )
        return file_name
        # return os.path.join(tempfile.gettempdir(), file_name)

    def get_year_data(self, year):
        ReportModel = get_report_model('v_year_totals_report')
        return ReportModel.objects.filter(year=year).all()

    def get_quarter_data(self, year):
        ReportModel = get_report_model('v_quarter_totals_report')
        return ReportModel.objects.filter(year=year).order_by('quarter', 'type')

    def get_month_data(self, year):
        ReportModel = get_report_model('v_month_totals_report')
        return ReportModel.objects.filter(year=year).order_by('month', 'type')

    def to_output(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {
            'in_memory': True,
            'default_date_format': 'dd/mm/yy',
            'remove_timezone': True
        })
        format_dark = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#555555',
            'align': 'center'
        })
        format_grey = workbook.add_format({'bg_color': '#DDDDDD'})
        border_bottom = workbook.add_format({'bottom': 1})

        year = 2017
        totals_worksheet = workbook.add_worksheet('Totals {}'.format(year))
        # data = self.get_totals_data(year)
        totals_worksheet.merge_range(0, 0, 0, 7, 'Period', format_dark)
        totals_worksheet.write(1, 0, 'Duration', format_grey)
        totals_worksheet.write(1, 1, 'Year', format_grey)
        totals_worksheet.write(1, 2, 'Quarter', format_grey)
        totals_worksheet.write(1, 3, 'Month', format_grey)
        totals_worksheet.write(1, 4, 'Week', format_grey)
        totals_worksheet.write(1, 5, 'Start date', format_grey)
        totals_worksheet.write(1, 6, 'End date', format_grey)

        totals_worksheet.merge_range(0, 7, 0, 10, 'Totals', format_dark)
        totals_worksheet.write(1, 7, 'Projects successful', format_grey)
        totals_worksheet.write(1, 8, 'Activities successful', format_grey)
        totals_worksheet.write(1, 9, 'Members volunteered', format_grey)
        totals_worksheet.write(1, 10, 'Hours volunteered', format_grey)

        # Rows for year
        start = datetime.date(year, 1, 1)
        end = datetime.date(year, 12, 31)
        totals_worksheet.write(2, 0, 'Year', border_bottom)
        totals_worksheet.write(2, 1, year, border_bottom)
        totals_worksheet.write(2, 2, '', border_bottom)
        totals_worksheet.write(2, 3, '', border_bottom)
        totals_worksheet.write(2, 4, '', border_bottom)
        totals_worksheet.write(2, 5, start, border_bottom)
        totals_worksheet.write(2, 6, end, border_bottom)

        year_data = self.get_year_data(year)
        for val in year_data:
            i = self.row_lookup[val.type] + 7
            totals_worksheet.write(2, int(i), val.value, border_bottom)

        # Rows for quarter
        for q in range(1, 5):
            start = datetime.date(year, q * 3 - 2, 1)
            end = datetime.date(year, q * 3, calendar.monthrange(year, q * 3)[1])
            totals_worksheet.write(2 + q, 0, 'Quarter')
            totals_worksheet.write(2 + q, 1, year)
            totals_worksheet.write(2 + q, 2, q)
            totals_worksheet.write(2 + q, 3, '')
            totals_worksheet.write(2 + q, 4, '')
            totals_worksheet.write(2 + q, 5, start)
            totals_worksheet.write(2 + q, 6, end)

        quarter_data = self.get_quarter_data(year)
        for val in quarter_data:
            i = self.row_lookup[val.type] + 7
            j = val.quarter + 2
            totals_worksheet.write(int(j), int(i), val.value)

        # Rows for months
        for m in range(1, 13):
            start = datetime.date(year, m, 1)
            end = datetime.date(year, m, calendar.monthrange(year, m)[1])
            totals_worksheet.write(6 + m, 0, 'Month')
            totals_worksheet.write(6 + m, 1, year)
            totals_worksheet.write(6 + m, 2, '')
            totals_worksheet.write(6 + m, 3, start.strftime('%B'))
            totals_worksheet.write(6 + m, 4, '')
            totals_worksheet.write(6 + m, 5, start)
            totals_worksheet.write(6 + m, 6, end)

        month_data = self.get_month_data(year)
        for val in month_data:
            i = self.row_lookup[val.type] + 7
            j = val.month + 6
            totals_worksheet.write(int(j), int(i), val.value)

        workbook.close()
        return output
