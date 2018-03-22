from django.urls.base import reverse
from django.utils.translation import ugettext_lazy as _

from jet.dashboard import modules
from jet.dashboard.dashboard import DefaultAppIndexDashboard
from jet.dashboard.modules import DashboardModule

from bluebottle.projects.models import Project


class RecentProjects(DashboardModule):
    title = _('Recently submitted projects')
    title_url = "{}?status_filter=2".format(reverse('admin:projects_project_changelist'))
    template = 'dashboard/recent_projects.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        projects = Project.objects.filter(status__slug='plan-submitted').order_by('date_submitted')
        self.children = projects[:self.limit]


class MyReviewingProjects(DashboardModule):
    title = _('Projects I\'m reviewing')
    title_url = "{}?reviewer=True".format(reverse('admin:projects_project_changelist'))
    template = 'dashboard/recent_projects.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        user = context.request.user
        self.children = Project.objects.filter(reviewer=user).order_by('-created')[:self.limit]


class ClosingFundingProjects(DashboardModule):
    title = _('Funding projects nearing deadline')
    title_url = "{}?o=6&status_filter=5".format(reverse('admin:projects_project_changelist'))
    template = 'dashboard/closing_funding_projects.html'
    limit = 5
    column = 1

    def init_with_context(self, context):
        self.children = Project.objects.filter(status__slug='campaign').order_by('deadline')[:self.limit]


class AppIndexDashboard(DefaultAppIndexDashboard):

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)
        self.children.append(RecentProjects())
        self.children.append(MyReviewingProjects())
        self.children.append(ClosingFundingProjects())
