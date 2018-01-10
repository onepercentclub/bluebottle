from admin_tools.dashboard.modules import DashboardModule
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from bluebottle.tasks.models import Task


class TaskModule(DashboardModule):
    """
    """
    title = _('Recently Created Tasks')
    template = 'admin_tools/dashboard/recent_tasks.html'
    limit = 10
    include_list = None
    exclude_list = None

    def __init__(self, title=None, limit=10, **kwargs):
        kwargs.update({'limit': limit})
        super(TaskModule, self).__init__(title, **kwargs)

    def init_with_context(self, context):
        qs = Task.objects.order_by('-created')

        self.children = qs[:self.limit]
        if not len(self.children):
            self.pre_content = _('No recent projects.')
        self._initialized = True


class RealizedTaskModule(TaskModule):
    """
    Custom class to display realized tasks that have taskmembers that are not realized. These are the tasks
    whereby the owner must still confirm that task members completed the tasks.
    """

    def init_with_context(self, context):
        try:
            qs = Task.objects.filter(status='realized').exclude(
                members__status__in=['realized']).distinct().order_by(
                self.order_by)
        except Exception:
            qs = []

        self.children = qs[:self.limit]
        for c in self.children:
            c.admin_url = reverse('admin:{0}_{1}_change'.format(
                Task._meta.app_label, Task._meta.module_name),
                args=(c.pk,))

        if not len(self.children):
            self.pre_content = _('No tasks found.')
        self._initialized = True


class RecentTasks(DashboardModule):
    """
    """
    title = _('Recently Created Tasks')
    template = 'admin_tools/dashboard/recent_tasks.html'
    limit = 10
    include_list = None
    exclude_list = None

    def __init__(self, title=None, limit=10, **kwargs):
        kwargs.update({'limit': limit})
        super(RecentTasks, self).__init__(title, **kwargs)

    def init_with_context(self, context):
        qs = Task.objects.order_by('-created')

        self.children = qs[:self.limit]
        if not len(self.children):
            self.pre_content = _('No recent projects.')
        self._initialized = True
