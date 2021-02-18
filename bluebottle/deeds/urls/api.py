from django.conf.urls import url

from bluebottle.deeds.views import DeedListView, DeedDetailView, DeedTransitionList


urlpatterns = [
    url(r'^/deed$',
        DeedListView.as_view(),
        name='deed-list'),

    url(r'^/deed/(?P<pk>\d+)$',
        DeedDetailView.as_view(),
        name='deed-detail'),

    url(r'^/deed/transitions$',
        DeedTransitionList.as_view(),
        name='deed-transition-list'),
]
