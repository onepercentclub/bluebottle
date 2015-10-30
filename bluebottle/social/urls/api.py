from bluebottle.social.views import AccessTokenView
from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'^(?P<backend>[^/]+)/$',
        AccessTokenView.as_view(),
        name='access-token')
)
