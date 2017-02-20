from admin_tools.dashboard.models import DashboardModule
from django.utils.translation import ugettext_lazy as _
from fluent_dashboard.dashboard import FluentIndexDashboard

from bluebottle.bb_tasks.dashboard import RecentTasks
from bluebottle.projects.dashboard import SubmittedPlans, EndedProjects, StartedCampaigns


class CustomIndexDashboard(FluentIndexDashboard):
    """
    Custom Dashboard for Bluebottle.
    """
    columns = 3

    def init_with_context(self, context):
        self.children.append(SubmittedPlans())
        self.children.append(StartedCampaigns())
        self.children.append(EndedProjects())
        self.children.append(RecentTasks())


class WallpostModule(DashboardModule):
    """
    Metrics module for the django admin tools dashboard.
    Since this is only meant to be here for a short while so lot's of simple hacks.
    """
    # FIXME: Replace with a decent metrics solution.
    title = _('Wallposts')
    template = 'admin_tools/dashboard/metrics_module.html'

    def __init__(self, **kwargs):
        mediawallpost_url = '/admin/wallposts/mediawallpost/'
        wallpost_url = '/admin/wallposts/wallpost/'

        self.children = (
            {'title': _('Media wallposts'), 'url': mediawallpost_url},
            {'title': _('All wallposts'), 'url': wallpost_url},

        )
        super(WallpostModule, self).__init__(**kwargs)
