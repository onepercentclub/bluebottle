from fluent_dashboard.dashboard import FluentIndexDashboard
from admin_tools.dashboard.modules import LinkList
from bluebottle.bb_tasks.dashboard import RecentTasks
from bluebottle.projects.dashboard import SubmittedPlans, EndedProjects, StartedCampaigns, Analytics
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _


class CustomIndexDashboard(FluentIndexDashboard):
    """
    Custom Dashboard for Bluebottle.
    """
    columns = 3

    def init_with_context(self, context):
        self.children.append(Analytics())
        self.children.append(SubmittedPlans())
        self.children.append(StartedCampaigns())
        self.children.append(EndedProjects())
        self.children.append(RecentTasks())
        if context['request'].user.has_perm('sites.export'):
            self.children.append(LinkList(
                _('Export Metrics'),
                children=[
                    {
                        'title': _('Export metrics'),
                        'url': reverse_lazy('exportdb_export'),
                    }
                ]
            ))
