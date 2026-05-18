from bluebottle.auth.views import SocialLoginView
from django.urls import path


urlpatterns = [
    path(
        'social-login',
        SocialLoginView.as_view(),
        name='social-login'
    ),
]
