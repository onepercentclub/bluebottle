from django.db.models import Subquery
from django.urls.base import reverse
from django.utils.translation import gettext_lazy as _
from jet.dashboard import modules
from jet.dashboard.dashboard import DefaultAppIndexDashboard
from jet.dashboard.modules import DashboardModule

from bluebottle.bluebottle_dashboard.utils import recent_log_entries
from bluebottle.activities.models import Activity, Contributor
from bluebottle.offices.admin import region_manager_filter


class UnPublishedActivities(DashboardModule):
    title = _('Unpublished activities')
    title_url = "{}?status[]=draft&status[]=needs_work".format(reverse('admin:activities_activity_changelist'))
    template = 'dashboard/unpublished_activities.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        activities = Activity.objects.filter(status__in=['draft', 'needs_work']).order_by('-created')
        user = context.request.user
        activities = region_manager_filter(activities, user)
        self.children = activities[:self.limit]


class RecentlySubmittedActivities(DashboardModule):
    title = _('Recently submitted activities')
    title_url = "{}?status[]=draft&status[]=open".format(reverse('admin:activities_activity_changelist'))
    template = 'dashboard/recent_activities.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        activities = Activity.objects.filter(
            status='submitted'
        ).annotate(
            transition_date=Subquery(recent_log_entries())
        ).order_by('transition_date')
        user = context.request.user
        activities = region_manager_filter(activities, user)
        self.children = activities[:self.limit]


class RecentlyPublishedActivities(DashboardModule):
    title = _('Recently published activities')
    title_url = "{}?status[]=open".format(reverse('admin:activities_activity_changelist'))
    template = 'dashboard/recent_activities.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        activities = Activity.objects.filter(
            status='open'
        ).annotate(
            transition_date=Subquery(recent_log_entries())
        ).order_by('transition_date')
        user = context.request.user
        activities = region_manager_filter(activities, user)
        self.children = activities[:self.limit]


class RecentContributors(DashboardModule):
    title = _('Recent contributions')
    title_url = "{}".format(reverse('admin:activities_contributor_changelist'))
    template = 'dashboard/recent_contributors.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        contributors = Contributor.objects.order_by('-created')
        user = context.request.user
        contributors = region_manager_filter(contributors, user)
        self.children = contributors[:self.limit]


class AppIndexDashboard(DefaultAppIndexDashboard):

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)
        self.children.append(RecentlySubmittedActivities())
        self.children.append(RecentlyPublishedActivities())
        self.children.append(RecentContributors())
