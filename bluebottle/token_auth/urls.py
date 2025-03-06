from django.urls import re_path
from bluebottle.token_auth.views import (
    MetadataView, TokenLogoutView,
    TokenRedirectView, UserSAMLLoginView, SupportSAMLLoginView,
    TokenErrorView
)


urlpatterns = [
    re_path(
        r'^redirect/$', TokenRedirectView.as_view(),
        name='token-redirect'
    ),
    re_path(
        r'^login/$', UserSAMLLoginView.as_view(),
        name='token-login'
    ),
    re_path(
        r'^support-login/$', SupportSAMLLoginView.as_view(),
        name='support-token-login'
    ),
    re_path(r'^logout/$', TokenLogoutView.as_view(), name='token-logout'),
    re_path(r'^error/$', TokenErrorView.as_view(), name='token-error'),
    re_path(r'^metadata/$', MetadataView.as_view(), name='token-metadata'),
]
