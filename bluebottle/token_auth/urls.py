from django.conf.urls import url

from bluebottle.token_auth.views import (
    MetadataView, TokenLogoutView,
    TokenRedirectView, TokenLoginView,
    TokenErrorView, MembersOnlyView,
    SupportTokenLoginView, SupportTokenLogoutView, SupportTokenErrorView,
    SupportMetadataView, SupportTokenRedirectView)

urlpatterns = [
    url(r'^redirect/$', TokenRedirectView.as_view(), name='token-redirect'),
    url(r'^login/(?P<token>.*?)$', TokenLoginView.as_view(), name='token-login'),
    url(r'^logout/$', TokenLogoutView.as_view(), name='token-logout'),
    url(r'^link/(?P<token>.+?)/(?P<link>.+?)$', TokenLoginView.as_view(), name='token-login-link'),
    url(r'^error/$', TokenErrorView.as_view(), name='token-error'),
    url(r'^missing/$', MembersOnlyView.as_view(), name='members-only'),
    url(r'^metadata/$', MetadataView.as_view(), name='token-metadata'),

    # Support SSO urls
    url(r'^support/login/(?P<token>.*?)$', SupportTokenLoginView.as_view(), name='support-token-login'),
    url(r'^support/logout/$', SupportTokenLogoutView.as_view(), name='support-token-logout'),
    url(r'^support/error/$', SupportTokenErrorView.as_view(), name='support-token-error'),
    url(r'^support/metadata/$', SupportMetadataView.as_view(), name='support-token-metadata'),
    url(r'^support/redirect/$', SupportTokenRedirectView.as_view(), name='support-token-redirect'),

]
