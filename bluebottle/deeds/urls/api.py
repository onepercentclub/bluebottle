from django.urls import re_path

from bluebottle.deeds.views import (
    DeedListView, DeedDetailView, DeedTransitionList,
    DeedRelatedParticipantList, ParticipantList, ParticipantDetail,
    ParticipantTransitionList, ParticipantExportView, DeedIcalView,
)


urlpatterns = [
    re_path(
        r'^$',
        DeedListView.as_view(),
        name='deed-list'
    ),

    re_path(
        r'^/(?P<pk>\d+)$',
        DeedDetailView.as_view(),
        name='deed-detail'
    ),

    re_path(
        r'^/transitions$',
        DeedTransitionList.as_view(),
        name='deed-transition-list'
    ),

    re_path(
        r'^/(?P<activity_id>\d+)/participants$',
        DeedRelatedParticipantList.as_view(),
        name='related-deed-participants'
    ),

    re_path(
        r'^/participants$',
        ParticipantList.as_view(),
        name='deed-participant-list'
    ),
    re_path(
        r'^/participants/(?P<pk>\d+)$',
        ParticipantDetail.as_view(),
        name='deed-participant-detail'
    ),
    re_path(
        r'^/participants/transitions$',
        ParticipantTransitionList.as_view(),
        name='deed-participant-transition-list'
    ),

    re_path(
        r'^/export/(?P<pk>[\d]+)$',
        ParticipantExportView.as_view(),
        name='deed-participant-export'
    ),

    re_path(
        r'^/ical/(?P<pk>\d+)$',
        DeedIcalView.as_view(),
        name='deed-ical'
    ),
]
