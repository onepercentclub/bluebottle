from django.conf.urls import url

from ..views import WebHookView

urlpatterns = [
    url(r'^webhook/$',
        WebHookView.as_view(),
        name='webhook'),
]
