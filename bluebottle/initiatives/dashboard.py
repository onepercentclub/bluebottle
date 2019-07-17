from django.urls.base import reverse
from django.utils.translation import ugettext_lazy as _
from jet.dashboard import modules
from jet.dashboard.dashboard import DefaultAppIndexDashboard
from jet.dashboard.modules import DashboardModule

from bluebottle.initiatives.models import Initiative


class RecentInitiatives(DashboardModule):
    title = _('Recently submitted initiatives')
    title_url = "{}?status__exact=submitted".format(reverse('admin:initiatives_initiative_changelist'))
    template = 'dashboard/recent_initiatives.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        initiatives = Initiative.objects.filter(status='submitted').order_by('-created')
        self.children = initiatives[:self.limit]


class MyReviewingInitiatives(DashboardModule):
    title = _("Initiatives I'm reviewing")
    title_url = "{}?reviewer=True".format(reverse('admin:initiatives_initiative_changelist'))
    template = 'dashboard/recent_initiatives.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        user = context.request.user
        self.children = Initiative.objects.filter(reviewer=user).order_by('-created')[:self.limit]


class AppIndexDashboard(DefaultAppIndexDashboard):

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)
        self.children.append(RecentInitiatives())
        self.children.append(MyReviewingInitiatives())
