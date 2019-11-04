from django.urls.base import reverse
from django.utils.translation import ugettext_lazy as _
from jet.dashboard import modules
from jet.dashboard.dashboard import DefaultAppIndexDashboard
from jet.dashboard.modules import DashboardModule

from bluebottle.assignments.models import Assignment


class RecentAssignments(DashboardModule):
    title = _('Recently submitted tasks')
    title_url = "{}?status[]=draft&status[]=open".format(reverse('admin:assignments_assignment_changelist'))
    template = 'dashboard/recent_assignments.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        activities = Assignment.objects.filter(status__in=['draft', 'open']).order_by('-created')
        self.children = activities[:self.limit]


class AppIndexDashboard(DefaultAppIndexDashboard):

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)
        self.children.append(RecentAssignments())
