from django.utils.translation import ugettext_lazy as _

from admin_tools.dashboard.modules import DashboardModule
from . import get_project_model


PROJECT_MODEL = get_project_model()


class ProjectModule(DashboardModule):
    """
    Generic project module for the django admin tools dashboard.
    """
    title = _('Projects')
    template = 'admin_tools/dashboard/project_module.html'
    limit = 10

    def __init__(self, title=None, limit=10, filter_kwargs=None, order_by=None, **kwargs):
        if order_by is None:
            order_by = '-created'
        self.order_by = order_by

        if filter_kwargs is None:
            filter_kwargs = {}
        self.filter_kwargs = filter_kwargs

        kwargs.update({'limit': limit})
        super(ProjectModule, self).__init__(title, **kwargs)

    def init_with_context(self, context):
        qs = PROJECT_MODEL.objects.filter(**self.filter_kwargs).order_by(self.order_by)

        self.children = qs[:self.limit]
        if not len(self.children):
            self.pre_content = _('No projects found.')
        self._initialized = True


class RecentProjects(ProjectModule):
    """
    Simple implementation of ``ProjectModule`` to show the most recent projects.
    """
    title = _('Recently Created Projects')
    template = 'admin_tools/dashboard/recent_projects.html'


class SubmittedProjects(ProjectModule):
    """
    Simple implementation of ``ProjectModule``
    TODO: This will not work for all projects. Left here for backwards-compat.
    """
    title = _('Recently Submitted Plans')
    template = 'admin_tools/dashboard/submitted_plans.html'

    def __init__(self, *args, **kwargs):
        kwargs.update({
            'filter_kwargs': {'status__name': 'Plan - Submitted'}
        })
        super(SubmittedProjects, self).__init__(*args, **kwargs)


class StartedCampaigns(ProjectModule):
    """
    Simple implementation of ``ProjectModule``
    TODO: This will not work for all projects. Left here for backwards-compat.
    """
    title = _('Recently Started Campaigns')
    template = 'admin_tools/dashboard/started_campaigns.html'

    def __init__(self, *args, **kwargs):
        kwargs.update({
            'filter_kwargs': {'status__name': 'Campaign'}
        })
        super(StartedCampaigns, self).__init__(*args, **kwargs)
