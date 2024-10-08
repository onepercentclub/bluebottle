from bluebottle.members.models import Member
from django.utils.translation import gettext_lazy as _
from django.urls.base import reverse

from jet.dashboard.modules import DashboardModule

from jet.dashboard import modules
from jet.dashboard.dashboard import DefaultAppIndexDashboard

from bluebottle.offices.admin import region_manager_filter


class RecentMembersDashboard(DashboardModule):
    title = _('Recently joined users')
    title_url = reverse('admin:members_member_changelist')
    template = 'dashboard/recent_members.html'
    limit = 5

    def init_with_context(self, context):
        members = Member.objects.order_by('-date_joined')
        user = context.request.user
        members = region_manager_filter(members, user)
        self.children = members[:self.limit]


class AppIndexDashboard(DefaultAppIndexDashboard):

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)
        self.children.append(RecentMembersDashboard())
