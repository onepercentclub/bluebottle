from django.urls.base import reverse
from django.utils.translation import gettext_lazy as _
from jet.dashboard import modules
from jet.dashboard.dashboard import DefaultAppIndexDashboard
from jet.dashboard.modules import DashboardModule

from bluebottle.wallposts.models import Wallpost


class RecentWallposts(DashboardModule):
    title = _('Recent wallposts')
    title_url = "{}".format(reverse('admin:wallposts_wallpost_changelist'))
    template = 'dashboard/recent_wallposts.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        wallposts = Wallpost.objects.order_by('-created')
        self.children = wallposts[:self.limit]


class AppIndexDashboard(DefaultAppIndexDashboard):

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)
