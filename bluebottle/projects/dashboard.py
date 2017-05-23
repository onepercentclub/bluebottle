from admin_tools.dashboard.modules import DashboardModule, LinkList
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.projects.models import Project


class RecentProjects(DashboardModule):
    title = _('Recently Created Projects')
    template = 'admin_tools/dashboard/recent_projects.html'
    limit = 10

    def __init__(self, title=None, limit=10, **kwargs):
        kwargs.update({'limit': limit})
        super(RecentProjects, self).__init__(title, **kwargs)

    def init_with_context(self, context):
        qs = Project.objects.order_by('-created')
        self.children = qs[:self.limit]
        if not len(self.children):
            self.pre_content = _('No recent projects.')
        self._initialized = True


class SubmittedPlans(DashboardModule):
    title = _('Recently Submitted Plans')
    template = 'admin_tools/dashboard/submitted_plans.html'
    limit = 10

    def __init__(self, title=None, limit=10, **kwargs):
        kwargs.update({'limit': limit})
        super(SubmittedPlans, self).__init__(title, **kwargs)

    def init_with_context(self, context):
        qs = Project.objects.order_by('created')
        qs = qs.filter(status=ProjectPhase.objects.get(slug="plan-submitted"))

        self.children = qs[:self.limit]
        if not len(self.children):
            self.pre_content = _('No submitted plans.')
        self._initialized = True


class StartedCampaigns(DashboardModule):
    title = _('Recently Started Projects')
    template = 'admin_tools/dashboard/started_campaigns.html'
    limit = 10

    def __init__(self, title=None, limit=10, **kwargs):
        kwargs.update({'limit': limit})
        super(StartedCampaigns, self).__init__(title, **kwargs)

    def init_with_context(self, context):
        qs = Project.objects.order_by('-created')
        qs = qs.filter(status=ProjectPhase.objects.get(slug="campaign"))

        self.children = qs[:self.limit]
        if not len(self.children):
            self.pre_content = _('No projects.')
        self._initialized = True


class EndedProjects(DashboardModule):
    title = _('Recently Ended Projects')
    template = 'admin_tools/dashboard/recent_ended_projects.html'
    limit = 10

    def __init__(self, title=None, limit=10, **kwargs):
        kwargs.update({'limit': limit})
        super(EndedProjects, self).__init__(title, **kwargs)

    def init_with_context(self, context):
        qs = Project.objects.filter(campaign_ended__isnull=False).order_by(
            '-campaign_ended')[:self.limit]
        projects = list(qs)

        self.children = projects[:self.limit]
        if not len(self.children):
            self.pre_content = _('No recently funded projects.')
        self._initialized = True


class Analytics(LinkList):
    title = _('Analytics')

    def __init__(self, title=None, **kwargs):
        self.children = ({'title': _('Analytics'),
                          'url': getattr(settings, 'ANALYTICS_FRONTEND', ''),
                          'external': True,
                          'description': _('Analytics'),
                          'attrs': {'target': '_blank'},
                          },)
        super(Analytics, self).__init__(title, **kwargs)
