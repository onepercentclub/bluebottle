from fluent_dashboard.dashboard import FluentIndexDashboard
from admin_tools.dashboard.modules import DashboardModule, LinkList
from bluebottle.bb_tasks.dashboard import RecentTasks
from bluebottle.projects.dashboard import SubmittedPlans, EndedProjects, StartedCampaigns, Analytics


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
