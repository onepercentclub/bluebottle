from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import re_path
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from jet.dashboard.dashboard import urls

from bluebottle.categories.models import Category
from bluebottle.geo.models import Location
from bluebottle.looker.models import LookerEmbed
from bluebottle.looker.utils import LookerSSOEmbed
from bluebottle.segments.models import SegmentType


@method_decorator(login_required, name='dispatch')
@method_decorator(
    permission_required('looker.access_looker_embeds', raise_exception=True),
    name='dispatch'
)
class LookerEmbedView(DetailView):
    template_name = 'dashboard/embed.html'
    queryset = LookerEmbed.objects.all()

    def get_context_data(self, **kwargs):
        context = super(LookerEmbedView, self).get_context_data(**kwargs)
        hide_filters = []

        if not Location.objects.exists():
            hide_filters.append('Work location')
            hide_filters.append('Work location group')
            hide_filters.append('Work location region')
            hide_filters.append('Member work location')
            hide_filters.append('Member work location group')
            hide_filters.append('Member work location region')
            hide_filters.append('Activity work location')
            hide_filters.append('Activity work location group')
            hide_filters.append('Activity work location region')

        if not Category.objects.exists():
            hide_filters.append('Category')

        if not SegmentType.objects.exists():
            hide_filters.append('Segment type')
            hide_filters.append('Segment')
            hide_filters.append('Member segment type')
            hide_filters.append('Member segment')
            hide_filters.append('Activity segment type')
            hide_filters.append('Activity segment')

        if settings.LOOKER_HOST and settings.LOOKER_SECRET:
            context['looker_embed_url'] = LookerSSOEmbed(
                self.request.user,
                type=context['object'].type,
                id=context['object'].looker_id,
                hide_filters=hide_filters
            ).url
        else:
            context['looker_embed_url'] = None
        return context


urls.register_urls([
    re_path(
        r'looker_embed/(?P<pk>[0-9]+)/$',
        LookerEmbedView.as_view(),
        name='looker-embed'
    )
])
