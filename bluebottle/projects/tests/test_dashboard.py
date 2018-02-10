# coding=utf-8
from django.test.client import RequestFactory

from tenant_schemas.urlresolvers import reverse

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class ProjectDashboardTest(BluebottleAdminTestCase):
    """
    Test member admin dashboard
    """

    def setUp(self):
        super(ProjectDashboardTest, self).setUp()
        self.init_projects()
        self.client.force_login(self.superuser)
        self.member_admin_url = reverse('admin:app_list', args=('projects', ))
        plan_new = ProjectPhase.objects.get(slug='plan-new')
        submitted = ProjectPhase.objects.get(slug='plan-submitted')
        needs_work = ProjectPhase.objects.get(slug='plan-needs-work')

        self.projects = ProjectFactory.create_batch(5, status=plan_new)

        self.projects[0].status = needs_work
        self.projects[0].reviewer = self.superuser
        self.projects[0].save()

        self.projects[1].status = needs_work
        self.projects[1].save()

        self.projects[2].status = submitted
        self.projects[2].save()

        self.request = RequestFactory().get(self.member_admin_url)
        self.request.user = self.superuser

    def test_project_dashboard(self):
        response = self.client.get(self.member_admin_url)
        self.assertContains(response, 'Recently submitted project')
        self.assertContains(response, 'Projects nearing deadline')

        # Project 2 is recently submitted
        self.assertContains(response, self.projects[2].title)
        # Project 3 is not recently submitted
        self.assertNotContains(response, self.projects[3].title)

        # Reviewer of Project 0
        self.assertContains(response, self.projects[0].title)
        # Not Reviewing Project 1
        self.assertNotContains(response, self.projects[1].title)
