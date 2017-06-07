import argparse
from datetime import datetime


def validate_date(date_string):
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return date_string
    except ValueError:
        msg = '{} is not a valid date or is not in the required date format YYYY-MM-DD'.format(date_string)
        raise argparse.ArgumentTypeError(msg)


def initialize_work_sheet(workbook, name, headers):
    worksheet = workbook.get_worksheet_by_name(name)
    if not worksheet:
        worksheet = workbook.add_worksheet(name)
        worksheet.write_row(0, 0, headers)
    return worksheet


def get_xls_file_name(prefix, start_date, end_date):
    return '{}_{}_{}_generated_{}.xlsx'.format(prefix,
                                               start_date.strftime("%Y%m%d"),
                                               end_date.strftime("%Y%m%d"),
                                               datetime.now().strftime("%Y%m%d-%H%M%S"))
