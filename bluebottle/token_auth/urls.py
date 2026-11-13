from django.urls import path
from bluebottle.token_auth.views import (
    MetadataView, TokenLogoutView,
    TokenRedirectView, UserSAMLLoginView, SupportSAMLLoginView,
    TokenErrorView
)


app_name = 'token-auth'

urlpatterns = [
    path(
        'redirect/', TokenRedirectView.as_view(),
        name='admin-saml-redirect'
    ),
    path(
        'redirect/<uuid:pk>/', TokenRedirectView.as_view(),
        name='saml-redirect'
    ),
    path(
        'login/<uuid:pk>/', UserSAMLLoginView.as_view(),
        name='saml-login'
    ),
    path(
        'support-login/', SupportSAMLLoginView.as_view(),
        name='support-saml-login'
    ),
    path('logout/<uuid:pk>/', TokenLogoutView.as_view(), name='saml-logout'),
    path('error/', TokenErrorView.as_view(), name='saml-error'),
    path('metadata/<uuid:pk>/', MetadataView.as_view(), name='saml-metadata'),
]
