from django.conf.urls import url
from bluebottle.token_auth.views import (
    MetadataView, TokenLogoutView,
    TokenRedirectView, TokenLoginView,
    TokenErrorView, MembersOnlyView
)


urlpatterns = [
    url(r'^redirect/$', TokenRedirectView.as_view(),
        name='token-redirect'),
    url(r'^login/(?P<token>.*?)$', TokenLoginView.as_view(),
        name='token-login'),
    url(r'^logout/$', TokenLogoutView.as_view(), name='token-logout'),
    url(r'^link/(?P<token>.+?)/(?P<link>.+?)$', TokenLoginView.as_view(),
        name='token-login-link'),
    url(r'^error/$', TokenErrorView.as_view(), name='token-error'),
    url(r'^missing/$', MembersOnlyView.as_view(), name='members-only'),
    url(r'^metadata/$', MetadataView.as_view(), name='token-metadata'),
]
