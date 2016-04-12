from admin_tools.dashboard.modules import DashboardModule
from bluebottle.utils.model_dispatcher import get_task_model
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

TASK_MODEL = get_task_model()


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
        qs = TASK_MODEL.objects.order_by('-created')

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
            qs = TASK_MODEL.objects.filter(status='realized').exclude(
                members__status__in=['realized']).distinct().order_by(
                self.order_by)
        except:
            qs = []

        self.children = qs[:self.limit]
        for c in self.children:
            c.admin_url = reverse('admin:{0}_{1}_change'.format(
                TASK_MODEL._meta.app_label, TASK_MODEL._meta.module_name),
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
        qs = TASK_MODEL.objects.order_by('-created')

        self.children = qs[:self.limit]
        if not len(self.children):
            self.pre_content = _('No recent projects.')
        self._initialized = True
