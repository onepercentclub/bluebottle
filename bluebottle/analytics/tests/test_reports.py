from bluebottle.analytics.reports import MetricsReport
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory
from bluebottle.test.utils import BluebottleTestCase, BluebottleAdminTestCase
from django.urls.base import reverse
from django.utils.timezone import now
from openpyxl.reader.excel import load_workbook


class TestReportExport(BluebottleTestCase):

    def test_report_export(self):
        campaign = ProjectPhase.objects.get(slug='done-complete')
        done = ProjectPhase.objects.get(slug='done-complete')
        projects = ProjectFactory.create_batch(10, status=campaign)
        tasks = TaskFactory.create_batch(10, project=projects[0], status='realized')
        TaskMemberFactory.create_batch(10, task=tasks[0], status='realized')
        for project in projects:
            project.status = done
            project.save()
        report = MetricsReport()
        result = report.to_output()
        wb = load_workbook(result)
        self.assertEqual(wb.active.title, 'Definitions')
        totals = wb.worksheets[1]
        self.assertEqual(totals.title, 'Totals {}'.format(now().year))


class TestDataExport(BluebottleAdminTestCase):

    def test_data_export(self):
        campaign = ProjectPhase.objects.get(slug='done-complete')
        done = ProjectPhase.objects.get(slug='done-complete')
        projects = ProjectFactory.create_batch(10, status=campaign)
        tasks = TaskFactory.create_batch(10, project=projects[0], status='realized')
        TaskMemberFactory.create_batch(10, task=tasks[0], status='realized')
        for project in projects:
            project.status = done
            project.save()

        self.client.force_login(self.superuser)
        url = reverse('exportdb_export')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
