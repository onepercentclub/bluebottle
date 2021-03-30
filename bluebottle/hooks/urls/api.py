from django.conf.urls import url

from bluebottle.hooks.views import LatestSignal, SignalList, SignalDetail

urlpatterns = [
    url(
        r'^/latest$',
        LatestSignal.as_view(),
        name='latest-signal'
    ),
    url(
        r'^/(?P<pk>[\d]+)$',
        SignalDetail.as_view(),
        name='signal-detail'
    ),
    url(
        r'^$',
        SignalList.as_view(),
        name='signal-list'
    ),
]
