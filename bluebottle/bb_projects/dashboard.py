from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext, ugettext_lazy as _

from admin_tools.dashboard.modules import DashboardModule
from bluebottle.utils.model_dispatcher import get_project_model, get_project_phaselog_model

PROJECT_MODEL = get_project_model()
PROJECT_PHASE_LOG_MODEL = get_project_phaselog_model()

class ProjectModule(DashboardModule):
    """
    Generic project module for the django admin tools dashboard.
    """
    title = _('Projects')
    template = 'admin_tools/dashboard/project_module.html'
    limit = 10

    def __init__(self, title=None, limit=10, filter_kwargs=None, order_by=None, **kwargs):
        if order_by is None:
            order_by = '-updated'
        self.order_by = order_by

        if filter_kwargs is None:
            filter_kwargs = {}
        self.filter_kwargs = filter_kwargs

        kwargs.update({'limit': limit})
        super(ProjectModule, self).__init__(title, **kwargs)

    def init_with_context(self, context):
        qs = PROJECT_MODEL.objects.filter(**self.filter_kwargs).order_by(self.order_by)
        self._paginate_and_urls(qs)

    def _paginate_and_urls(self, qs):

        self.children = qs[:self.limit]
        for c in self.children:
            c.admin_url = reverse('admin:{0}_{1}_change'.format(
                PROJECT_MODEL._meta.app_label, PROJECT_MODEL._meta.module_name), args=(c.pk,))

        if not len(self.children):
            self.pre_content = _('No projects found.')
        self._initialized = True

    @property
    def post_content(self):
        url = reverse('admin:{0}_{1}_changelist'.format(PROJECT_MODEL._meta.app_label, PROJECT_MODEL._meta.module_name))
        return mark_safe('<a href="{0}">{1}</a>'.format(url, ugettext('View all projects')))


class SubmitAfterNeed(ProjectModule):
    title = _('Recently submitted Projects after needs-to-work')
    template = 'admin_tools/dashboard/project_module.html'

    def init_with_context(self, context):
        # all the projects in submit phase
        qs = PROJECT_MODEL.objects.filter(**self.filter_kwargs).order_by(self.order_by)

        submitted_project_log = []
        for project in qs:
            # I take the ones which have a need work phase in the log
            project_log = PROJECT_PHASE_LOG_MODEL.objects.filter(project=project, status__name="Plan - Needs Work").distinct('project')
            if project_log:
                submitted_project_log.append(project_log.get())
        # let's sort that
        submitted_project_log.sort(key=lambda x: x.start, reverse=True)

        # and get the project out
        submitted_project = [x.project for x in submitted_project_log]
        self._paginate_and_urls(submitted_project)


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
    TODO: IT'S WRONG, it analyze the creation date not the status changed date
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
    title = _('Recently Started Projects')
    template = 'admin_tools/dashboard/started_campaigns.html'

    def __init__(self, *args, **kwargs):
        kwargs.update({
            'filter_kwargs': {'status__name': 'Campaign'}
        })
        super(StartedCampaigns, self).__init__(*args, **kwargs)
