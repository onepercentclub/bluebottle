from django.urls import path
from bluebottle.token_auth.views import (
    MetadataView, TokenLogoutView,
    TokenRedirectView, UserSAMLLoginView, SupportSAMLLoginView,
    TokenErrorView
)


app_name = 'token-auth'

urlpatterns = [
    path(
        'redirect/<int:pk>/', TokenRedirectView.as_view(),
        name='saml-redirect'
    ),
    path(
        'login/', UserSAMLLoginView.as_view(),
        name='saml-login'
    ),
    path(
        'support-login/', SupportSAMLLoginView.as_view(),
        name='support-saml-login'
    ),
    path('logout/', TokenLogoutView.as_view(), name='saml-logout'),
    path('error/', TokenErrorView.as_view(), name='saml-error'),
    path('metadata/<int:pk>/', MetadataView.as_view(), name='saml-metadata'),
]
