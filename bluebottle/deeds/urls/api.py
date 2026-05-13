from django.urls import path
from django.urls import re_path

from bluebottle.deeds.views import (
    DeedListView, DeedDetailView, DeedTransitionList,
    DeedRelatedParticipantList, ParticipantList, ParticipantDetail,
    ParticipantTransitionList, ParticipantExportView, DeedIcalView,
)


urlpatterns = [
    path(
        '',
        DeedListView.as_view(),
        name='deed-list'
    ),

    path(
        '/<int:pk>',
        DeedDetailView.as_view(),
        name='deed-detail'
    ),

    path(
        '/transitions',
        DeedTransitionList.as_view(),
        name='deed-transition-list'
    ),

    path(
        '/<int:activity_id>/participants',
        DeedRelatedParticipantList.as_view(),
        name='related-deed-participants'
    ),

    path(
        '/participants',
        ParticipantList.as_view(),
        name='deed-participant-list'
    ),
    path(
        '/participants/<int:pk>',
        ParticipantDetail.as_view(),
        name='deed-participant-detail'
    ),
    path(
        '/participants/transitions',
        ParticipantTransitionList.as_view(),
        name='deed-participant-transition-list'
    ),

    re_path(
        r'^/export/(?P<pk>[\d]+)$',
        ParticipantExportView.as_view(),
        name='deed-participant-export'
    ),

    path(
        '/ical/<int:pk>',
        DeedIcalView.as_view(),
        name='deed-ical'
    ),
]
