from django.conf.urls import url

from bluebottle.deeds.views import (
    DeedListView, DeedDetailView, DeedTransitionList,
    DeedRelatedParticipantList, ParticipantList, ParticipantDetail,
    ParticipantTransitionList
)


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

    url(r'^/(?P<activity_id>\d+)/participants$',
        DeedRelatedParticipantList.as_view(),
        name='related-deed-participants'),

    url(r'^/participants$',
        ParticipantList.as_view(),
        name='deed-participant-list'),
    url(r'^/participants/(?P<pk>\d+)$',
        ParticipantDetail.as_view(),
        name='deed-participant-detail'),
    url(r'^/participants/transitions$',
        ParticipantTransitionList.as_view(),
        name='deed-participant-transition-list'),
]
