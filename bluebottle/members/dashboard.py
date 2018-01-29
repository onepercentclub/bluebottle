from bluebottle.members.models import Member
from django.utils.translation import ugettext_lazy as _
from django.urls.base import reverse

from jet.dashboard.modules import DashboardModule

from jet.dashboard import modules
from jet.dashboard.dashboard import DefaultAppIndexDashboard


class RecentMembers(DashboardModule):
    title = _('Recently Joined Members')
    title_url = reverse('admin:members_member_changelist')
    template = 'dashboard/recent_members.html'
    limit = 5

    def init_with_context(self, context):
        projects = Member.objects.order_by('-date_joined')
        self.children = projects[:self.limit]


class AppIndexDashboard(DefaultAppIndexDashboard):

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)
        self.children.append(RecentMembers())
