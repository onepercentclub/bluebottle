from django.urls.base import reverse
from django.db.models import Subquery
from django.utils.translation import gettext_lazy as _
from jet.dashboard import modules
from jet.dashboard.dashboard import DefaultAppIndexDashboard
from jet.dashboard.modules import DashboardModule

from bluebottle.bluebottle_dashboard.utils import recent_log_entries
from bluebottle.initiatives.models import Initiative
from bluebottle.offices.admin import region_manager_filter


class RecentlySubmittedInitiatives(DashboardModule):
    title = _('Recently submitted initiatives')
    title_url = "{}?status[]=draft&status[]=needs_work".format(
        reverse('admin:initiatives_initiative_changelist')
    )
    template = 'dashboard/recent_initiatives.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        initiatives = Initiative.objects.filter(
            status='submitted'
        ).annotate(
            transition_date=Subquery(recent_log_entries(polymorpic=False))
        ).order_by('transition_date')
        user = context.request.user
        initiatives = region_manager_filter(initiatives, user)
        self.children = initiatives[:self.limit]


class RecentlyPublishedInitiatives(DashboardModule):
    title = _('Recently published initiatives')
    title_url = "{}?status[]=approved".format(reverse('admin:initiatives_initiative_changelist'))
    template = 'dashboard/recent_initiatives.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        initiatives = Initiative.objects.filter(
            status='approved'
        ).annotate(
            transition_date=Subquery(recent_log_entries(polymorpic=False))
        ).order_by('transition_date')
        user = context.request.user
        initiatives = region_manager_filter(initiatives, user)
        self.children = initiatives[:self.limit]


class MyReviewingInitiatives(DashboardModule):
    title = _("Initiatives I'm reviewing")
    title_url = "{}?reviewer=True".format(reverse('admin:initiatives_initiative_changelist'))
    template = 'dashboard/recent_initiatives.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        if getattr(context, 'request', None):
            user = context.request.user
            self.children = Initiative.objects.filter(reviewer=user).order_by('-created')[:self.limit]


class AppIndexDashboard(DefaultAppIndexDashboard):

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)
        self.children.append(RecentlySubmittedInitiatives())
        self.children.append(RecentlyPublishedInitiatives())
        self.children.append(MyReviewingInitiatives())
