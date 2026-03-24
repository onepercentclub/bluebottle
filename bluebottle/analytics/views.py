from django.contrib.auth.decorators import login_required, permission_required
from django.urls import re_path
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from jet.dashboard.dashboard import urls

from bluebottle.analytics.models import AnalyticsPlatformSettings


@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("looker.access_looker_embeds", raise_exception=True),
    name="dispatch",
)
class PlausibleEmbedView(DetailView):
    template_name = "dashboard/plausible_embed.html"

    def get_object(self, queryset=None):
        settings = AnalyticsPlatformSettings.load()
        return settings


urls.register_urls(
    [re_path(r"plausible_embed/$", PlausibleEmbedView.as_view(), name="plausible-embed")]
)
