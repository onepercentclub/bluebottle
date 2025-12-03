from bluebottle.auth.views import SocialLoginView
from django.urls import re_path


urlpatterns = [
    re_path(
        r'^social-login$',
        SocialLoginView.as_view(),
        name='social-login'
    ),
]
