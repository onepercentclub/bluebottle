from django.urls.base import reverse
from django.utils.translation import gettext_lazy as _
from jet.dashboard import modules
from jet.dashboard.dashboard import DefaultAppIndexDashboard
from jet.dashboard.modules import DashboardModule

from bluebottle.offices.admin import region_manager_filter
from bluebottle.updates.models import Update


class RecentUpdates(DashboardModule):
    title = _('Recent wall updates')
    title_url = "{}".format(reverse('admin:updates_update_changelist'))
    template = 'dashboard/recent_updates.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        updates = Update.objects.order_by('-created')
        user = context['request'].user
        updates = region_manager_filter(updates, user)
        self.children = updates[:self.limit]


class AppIndexDashboard(DefaultAppIndexDashboard):

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)
        self.children.append(RecentUpdates())
