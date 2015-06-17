from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from fluent_dashboard.dashboard import FluentIndexDashboard, modules
from bluebottle.projects.dashboard import SubmittedPlans, EndedProjects, StartedCampaigns
from bluebottle.bb_tasks.dashboard import RecentTasks


class CustomIndexDashboard(FluentIndexDashboard):
    """
    Custom Dashboard for onepercentclub-site.
    """
    columns = 3

    def init_with_context(self, context):
        self.children.append(SubmittedPlans())
        self.children.append(StartedCampaigns())
        self.children.append(EndedProjects())
        self.children.append(RecentTasks())

        self.children.append(modules.LinkList(
            _('Metrics'),
            children=[
                {
                    'title': _('Export metrics'),
                    'url': reverse_lazy('exportdb_export'),
                }
            ]
        ))
