from django.urls import path
from bluebottle.token_auth.views import (
    MetadataView, TokenLogoutView,
    TokenRedirectView, SAMLLoginView,
    TokenErrorView
)


app_name = 'token-auth'

urlpatterns = [
    path(
        'redirect/<uuid:pk>/', TokenRedirectView.as_view(),
        name='saml-redirect'
    ),
    path(
        'login/', SAMLLoginView.as_view(),
        name='saml-login'
    ),
    path(
        'support-login/', SAMLLoginView.as_view(),
        name='support-login'
    ),
    path('logout/', TokenLogoutView.as_view(), name='saml-logout'),
    path('error/', TokenErrorView.as_view(), name='saml-error'),
    path('metadata/<uuid:pk>/', MetadataView.as_view(), name='saml-metadata'),
]
