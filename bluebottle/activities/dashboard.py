from django.urls.base import reverse
from django.utils.translation import ugettext_lazy as _
from jet.dashboard import modules
from jet.dashboard.dashboard import DefaultAppIndexDashboard
from jet.dashboard.modules import DashboardModule

from bluebottle.activities.models import Activity


class RecentActivities(DashboardModule):
    title = _('Recently submitted activities')
    title_url = "{}?status[]=draft&status[]=open".format(reverse('admin:activities_activity_changelist'))
    template = 'dashboard/recent_activities.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        activities = Activity.objects.filter(review_status__in=['submitted']).order_by('-created')
        self.children = activities[:self.limit]


class AppIndexDashboard(DefaultAppIndexDashboard):

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)
        self.children.append(RecentActivities())
