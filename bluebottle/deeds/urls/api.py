from django.conf.urls import url

from bluebottle.deeds.views import DeedListView, DeedDetailView, DeedTransitionList


urlpatterns = [
    url(r'^/$',
        DeedListView.as_view(),
        name='deed-list'),

    url(r'^/(?P<pk>\d+)$',
        DeedDetailView.as_view(),
        name='deed-detail'),

    url(r'^/transitions$',
        DeedTransitionList.as_view(),
        name='deed-transition-list'),
]
