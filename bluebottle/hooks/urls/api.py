from django.conf.urls import url

from bluebottle.hooks.views import LatestSignal

urlpatterns = [
    url(
        r'^/latest$',
        LatestSignal.as_view(),
        name='latest-signal'
    ),
]
