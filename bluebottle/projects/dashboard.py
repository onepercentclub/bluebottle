from django.utils.translation import ugettext_lazy as _

from admin_tools.dashboard.modules import DashboardModule

from . import get_project_model

PROJECT_MODEL = get_project_model()


class RecentProjects(DashboardModule):
    title = _('Recently Created Projects')
    template = 'admin_tools/dashboard/recent_projects.html'
    limit = 10

    def __init__(self, title=None, limit=10, **kwargs):
        kwargs.update({'limit': limit})
        super(RecentProjects, self).__init__(title, **kwargs)

    def init_with_context(self, context):
        qs = PROJECT_MODEL.objects.order_by('-created')
        self.children = qs[:self.limit]
        if not len(self.children):
            self.pre_content = _('No recent projects.')
        self._initialized = True


class SubmittedProjects(DashboardModule):
    title = _('Recently Submitted Plans')
    template = 'admin_tools/dashboard/submitted_plans.html'
    limit = 10

    def __init__(self, title=None, limit=10, **kwargs):
        kwargs.update({'limit': limit})
        super(SubmittedProjects, self).__init__(title, **kwargs)

    def init_with_context(self, context):
        qs = PROJECT_MODEL.objects.order_by('created')
        qs = qs.filter(phase='plan-submitted')

        self.children = qs[:self.limit]
        if not len(self.children):
            self.pre_content = _('No submitted plans.')
        self._initialized = True


class StartedCampaigns(DashboardModule):
    title = _('Recently Started Campaigns')
    template = 'admin_tools/dashboard/started_campaigns.html'
    limit = 10

    def __init__(self, title=None, limit=10, **kwargs):
        kwargs.update({'limit': limit})
        super(StartedCampaigns, self).__init__(title, **kwargs)

    def init_with_context(self, context):
        qs = PROJECT_MODEL.objects.order_by('-created')
        qs = qs.filter(phase='campaign-running')

        self.children = qs[:self.limit]
        if not len(self.children):
            self.pre_content = _('No campaigns.')
        self._initialized = True

