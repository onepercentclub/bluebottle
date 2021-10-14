import os

import xlsxwriter
from django.http import HttpResponse


def generate_xlsx(filename, data):
    workbook = xlsxwriter.Workbook(filename, {'remove_timezone': True})
    worksheet = workbook.add_worksheet()
    for t, row in enumerate(data):
        worksheet.write_row(t, 0, row)
    workbook.close()
    return filename


def generate_xlsx_response(filename, data):
    filename = generate_xlsx(filename, data)
    file_path = os.path.join(os.path.dirname(os.path.realpath(__name__)), filename)
    response = HttpResponse(open(file_path, 'rb').read())
    response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
