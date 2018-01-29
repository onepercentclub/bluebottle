from django.views.generic.base import TemplateView

from bluebottle.utils.utils import get_current_host


class AnalyticsView(TemplateView):

    template_name = 'analytics/index.html'

    def get_context_data(self, **kwargs):
        context = super(AnalyticsView, self).get_context_data(**kwargs)
        # We need this so 'View Site' shows in admin menu
        context['site_url'] = get_current_host()
        return context
