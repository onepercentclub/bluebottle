from bluebottle.analytics.reports import MetricsReport
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase
from django.utils.timezone import now
from openpyxl.reader.excel import load_workbook


class TestReportExport(BluebottleTestCase):

    def test_report_export(self):
        ProjectFactory.create_batch(12)
        report = MetricsReport()
        result = report.to_output()
        wb = load_workbook(result)
        self.assertEqual(wb.active.title, 'Definitions')
        totals = wb.worksheets[1]
        self.assertEqual(totals.title, 'Totals {}'.format(now().year))
