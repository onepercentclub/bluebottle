from bluebottle.social.views import AccessTokenView
from django.conf.urls import url


urlpatterns = [
    url(r'^(?P<backend>[^/]+)/$',
        AccessTokenView.as_view(),
        name='access-token')
]
