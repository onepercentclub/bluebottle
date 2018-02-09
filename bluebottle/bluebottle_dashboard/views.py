from django.views.generic.base import TemplateView

from bluebottle.utils.utils import get_current_host


class AnalyticsView(TemplateView):

    template_name = 'analytics/index.html'

    mapping = {
        'users': 16,
        'projects': 18,

        'volunteers': 19,
        'tasks': 21,
        'hours': 20,

        'donations': 17,
        'supporters': 22,

        'voting': 16,

    }

    def get_context_data(self, **kwargs):
        context = super(AnalyticsView, self).get_context_data(**kwargs)
        # We need this so 'View Site' shows in admin menu
        context['site_url'] = get_current_host()
        context['report_id'] = self.mapping[kwargs['report']]
        return context
