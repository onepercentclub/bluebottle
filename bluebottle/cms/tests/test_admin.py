from django.urls.base import reverse

from fluent_contents.models import Placeholder

from bluebottle.cms.models import MetricsContent, TasksContent
from bluebottle.test.factory_models.cms import ResultPageFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class TestResultPageAdmin(BluebottleAdminTestCase):
    def setUp(self):
        super(TestResultPageAdmin, self).setUp()
        self.client.force_login(self.superuser)
        self.init_projects()

    def test_add_results_page(self):
        result_page_url = reverse('admin:cms_resultpage_add')
        response = self.client.get(result_page_url)
        self.assertEqual(response.status_code, 200)

    def test_change_results_page(self):
        result_page = ResultPageFactory.create()
        self.placeholder = Placeholder.objects.create_for_object(result_page, slot='content')
        MetricsContent.objects.create_for_placeholder(self.placeholder, title='Look at us!')
        TasksContent.objects.create_for_placeholder(self.placeholder, title='Look at us!')
        result_page_url = reverse('admin:cms_resultpage_change', args=(result_page.id, ))
        response = self.client.get(result_page_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Metrics')
        self.assertContains(response, 'Tasks')
