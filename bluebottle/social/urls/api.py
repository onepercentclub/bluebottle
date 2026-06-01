from bluebottle.social.views import AccessTokenView
from django.urls import path


urlpatterns = [
    path(
        '<str:backend>/',
        AccessTokenView.as_view(),
        name='access-token'
    )
]
