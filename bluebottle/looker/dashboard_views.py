from bluebottle.segments.models import SegmentType

from bluebottle.categories.models import Category

from bluebottle.geo.models import Location
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import re_path
from django.views.generic import DetailView
from django.utils.decorators import method_decorator

from jet.dashboard.dashboard import urls

from bluebottle.looker.models import LookerEmbed
from bluebottle.looker.utils import LookerSSOEmbed


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
            hide_filters.append('Office')
            hide_filters.append('Office group')
            hide_filters.append('Office region')
            hide_filters.append('Member office')
            hide_filters.append('Member office group')
            hide_filters.append('Member office region')
            hide_filters.append('Activity office')
            hide_filters.append('Activity office group')
            hide_filters.append('Activity office region')

        if not Category.objects.exists():
            hide_filters.append('Category')

        if not SegmentType.objects.exists():
            hide_filters.append('Segment type')
            hide_filters.append('Segment')
            hide_filters.append('Member segment type')
            hide_filters.append('Member segment')
            hide_filters.append('Activity segment type')
            hide_filters.append('Activity segment')

        context['looker_embed_url'] = LookerSSOEmbed(
            self.request.user,
            type=context['object'].type,
            id=context['object'].looker_id,
            hide_filters=hide_filters
        ).url
        return context


urls.register_urls([
    re_path(
        r'looker_embed/(?P<pk>[0-9]+)/$',
        LookerEmbedView.as_view(),
        name='looker-embed'
    )
])
