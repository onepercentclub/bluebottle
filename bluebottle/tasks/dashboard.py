from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext, ugettext_lazy as _

from admin_tools.dashboard.modules import DashboardModule

from bluebottle.tasks import get_task_model


TASK_MODEL = get_task_model()


class TaskModule(DashboardModule):
    """
    Generic task module for the django admin tools dashboard.
    """
    title = _('Tasks')
    template = 'admin_tools/dashboard/task_module.html'
    limit = 10

    def __init__(self, title=None, limit=10, filter_kwargs=None, order_by=None, **kwargs):
        if order_by is None:
            order_by = '-created'
        self.order_by = order_by

        if filter_kwargs is None:
            filter_kwargs = {}
        self.filter_kwargs = filter_kwargs

        kwargs.update({'limit': limit})
        super(TaskModule, self).__init__(title, **kwargs)

    def init_with_context(self, context):
        qs = TASK_MODEL.objects.filter(**self.filter_kwargs).order_by(self.order_by)

        self.children = qs[:self.limit]
        if not len(self.children):
            self.pre_content = _('No tasks found.')
        self._initialized = True

    @property
    def post_content(self):
        url = reverse('admin:{0}_{1}_changelist'.format(TASK_MODEL._meta.app_label, TASK_MODEL._meta.module_name))
        return mark_safe('<a href="{0}">{1}</a>'.format(url, ugettext('View all tasks')))


class RecentTasks(TaskModule):
    """
    Simple implementation of ``TaskModule`` to keep existing BlueBottle projects working.
    """
    title = _('Recently Created Tasks')
    template = 'admin_tools/dashboard/recent_tasks.html'
