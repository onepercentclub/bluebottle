from django.urls import re_path
from bluebottle.token_auth.views import (
    MetadataView, TokenLogoutView,
    TokenRedirectView, TokenLoginView,
    TokenErrorView, MembersOnlyView
)


urlpatterns = [
    re_path(r'^redirect/$', TokenRedirectView.as_view(),
        name='token-redirect'),
    re_path(r'^login/(?P<token>.*?)$', TokenLoginView.as_view(),
        name='token-login'),
    re_path(r'^logout/$', TokenLogoutView.as_view(), name='token-logout'),
    re_path(r'^link/(?P<token>.+?)/(?P<link>.+?)$', TokenLoginView.as_view(),
        name='token-login-link'),
    re_path(r'^error/$', TokenErrorView.as_view(), name='token-error'),
    re_path(r'^missing/$', MembersOnlyView.as_view(), name='members-only'),
    re_path(r'^metadata/$', MetadataView.as_view(), name='token-metadata'),
]
