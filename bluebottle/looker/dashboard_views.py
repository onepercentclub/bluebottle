from django.conf.urls import url
from django.views.generic import DetailView
from jet.dashboard.dashboard import urls

from bluebottle.looker.models import LookerEmbed
from bluebottle.looker.utils import LookerSSOEmbed


class LookerEmbedView(DetailView):
    template_name = 'dashboard/embed.html'
    queryset = LookerEmbed.objects.all()

    def get_context_data(self, **kwargs):
        context = super(LookerEmbedView, self).get_context_data(**kwargs)
        context['looker_embed_url'] = LookerSSOEmbed(
            self.request.user,
            type=context['object'].type,
            id=context['object'].looker_id,
        ).url

        return context


urls.register_urls([
    url(
        r'looker_embed/(?P<pk>[0-9]+)/$',
        LookerEmbedView.as_view(),
        name='looker-embed'
    )
])
