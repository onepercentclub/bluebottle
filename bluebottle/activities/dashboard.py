from django.urls.base import reverse
from django.utils.translation import gettext_lazy as _
from jet.dashboard import modules
from jet.dashboard.dashboard import DefaultAppIndexDashboard
from jet.dashboard.modules import DashboardModule

from bluebottle.activities.models import Activity, Contributor
from bluebottle.time_based.models import PeriodActivity


class UnPublishedActivities(DashboardModule):
    title = _('Unpublished activities')
    title_url = "{}?status[]=draft&status[]=needs_work".format(reverse('admin:activities_activity_changelist'))
    template = 'dashboard/unpublished_activities.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        activities = Activity.objects.filter(status__in=['draft', 'needs_work']).order_by('-created')
        self.children = activities[:self.limit]


class RecentActivities(DashboardModule):
    title = _('Recently submitted activities')
    title_url = "{}?status[]=draft&status[]=open".format(reverse('admin:activities_activity_changelist'))
    template = 'dashboard/recent_activities.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        # Temporary fix until we ge rid of PeriodActivity
        activities = (
            Activity.objects.not_instance_of(PeriodActivity)
            .filter(status="submitted")
            .order_by("-created")
        )
        self.children = activities[: self.limit]


class RecentContributors(DashboardModule):
    title = _('Recent contributions')
    title_url = "{}".format(reverse('admin:activities_contributor_changelist'))
    template = 'dashboard/recent_contributors.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        contributors = Contributor.objects.order_by('-created')
        self.children = contributors[:self.limit]


class AppIndexDashboard(DefaultAppIndexDashboard):

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)
        self.children.append(RecentActivities())
        self.children.append(RecentContributors())
