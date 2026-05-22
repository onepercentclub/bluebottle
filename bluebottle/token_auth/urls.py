from django.urls import path
from bluebottle.token_auth.views import (
    MetadataView, TokenLogoutView,
    TokenRedirectView, UserSAMLLoginView, SupportSAMLLoginView,
    TokenErrorView
)


urlpatterns = [
    path(
        'redirect/', TokenRedirectView.as_view(),
        name='token-redirect'
    ),
    path(
        'login/', UserSAMLLoginView.as_view(),
        name='token-login'
    ),
    path(
        'support-login/', SupportSAMLLoginView.as_view(),
        name='support-token-login'
    ),
    path('logout/', TokenLogoutView.as_view(), name='token-logout'),
    path('error/', TokenErrorView.as_view(), name='token-error'),
    path('metadata/', MetadataView.as_view(), name='token-metadata'),
]
