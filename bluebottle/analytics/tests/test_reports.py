from bluebottle.analytics.reports import MetricsReport
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.tasks import TaskFactory
from bluebottle.test.utils import BluebottleTestCase
from django.utils.timezone import now
from openpyxl.reader.excel import load_workbook


class TestReportExport(BluebottleTestCase):

    def test_report_export(self):
        campaign = ProjectPhase.objects.get(slug='done-complete')
        done = ProjectPhase.objects.get(slug='done-complete')
        projects = ProjectFactory.create_batch(10, status=campaign)
        TaskFactory.create_batch(12, project=projects[0])
        for project in projects:
            project.status = done
            project.save()
        report = MetricsReport()
        result = report.to_output()
        wb = load_workbook(result)
        self.assertEqual(wb.active.title, 'Definitions')
        totals = wb.worksheets[1]
        self.assertEqual(totals.title, 'Totals {}'.format(now().year))
