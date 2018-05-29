from django.utils.translation import ugettext_lazy as _

from jet.dashboard.modules import DashboardModule
from jet.dashboard.dashboard import DefaultAppIndexDashboard

from bluebottle.looker.models import LookerEmbed


class LookerDashboard(DashboardModule):
    title = _('Analytics')
    template = 'dashboard/looker.html'
    limit = 5

    def init_with_context(self, context):
        self.children = LookerEmbed.objects.all()


class AppIndexDashboard(DefaultAppIndexDashboard):
    def init_with_context(self, context):
        self.children.append(LookerDashboard())
