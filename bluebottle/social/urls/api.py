from bluebottle.social.views import AccessTokenView
from django.urls import re_path


urlpatterns = [
    re_path(r'^(?P<backend>[^/]+)/$',
        AccessTokenView.as_view(),
        name='access-token')
]
