import importlib

from bluebottle.members.dashboard import RecentMembersDashboard
from bluebottle.projects.dashboard import RecentProjects, MyReviewingProjects, ClosingFundingProjects
from django.urls.base import reverse, reverse_lazy
from django.utils.timezone import now
from django.utils.translation import ugettext as _

from jet.dashboard import modules
from jet.dashboard.dashboard import Dashboard, DefaultAppIndexDashboard
from jet.dashboard.modules import DashboardModule, LinkList

from bluebottle.clients import properties
from bluebottle.tasks.models import Task


class ClosingTasks(DashboardModule):
    title = _('Tasks nearing application deadline')
    title_url = reverse('admin:tasks_task_changelist')
    template = 'dashboard/closing_tasks.html'
    limit = 5

    def init_with_context(self, context):
        tasks = Task.objects.exclude(deadline_to_apply__lt=now()).\
            filter(project__status__slug='campaign').\
            filter(status__in=['open', 'full']).order_by('deadline_to_apply')
        self.children = tasks[:self.limit]


class CustomIndexDashboard(Dashboard):
    columns = 2

    class Media:
        css = ('css/admin/dashboard.css', )

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)
        self.children.append(RecentProjects())
        self.children.append(MyReviewingProjects())
        self.children.append(ClosingFundingProjects())
        self.children.append(ClosingTasks())
        self.children.append(RecentMembersDashboard())
        if context['request'].user.has_perm('sites.export'):
            metrics_children = [
                {
                    'title': _('Export metrics'),
                    'url': reverse_lazy('exportdb_export'),
                },
            ]
            if properties.REPORTING_BACKOFFICE_ENABLED:
                metrics_children.append({
                    'title': _('Download report'),
                    'url': reverse_lazy('report-export'),
                })

            if properties.PARTICIPATION_BACKOFFICE_ENABLED:
                metrics_children.append({
                    'title': _('Request complete participation metrics'),
                    'url': reverse('participation-metrics')
                })

            self.children.append(LinkList(
                _('Export Metrics'),
                children=metrics_children
            ))


class CustomAppIndexDashboard(DefaultAppIndexDashboard):

    def __new__(cls, context, **kwargs):
        try:
            mod = importlib.import_module("bluebottle.{}.dashboard".format(kwargs['app_label']))
            dash = mod.AppIndexDashboard(context, **kwargs)
            return dash
        except ImportError:
            return DefaultAppIndexDashboard(context, **kwargs)
