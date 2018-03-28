from django.contrib.auth.decorators import login_required, permission_required
from django.conf.urls import url
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
