from django.urls import path
from django.urls import re_path

from bluebottle.time_based.views import (
    RegisteredDateTransitionList,
    RegisteredDateActivityListView, RegisteredDateActivityDetailView,
    RegisteredDateParticipantTransitionList, RegisteredDateParticipantExportView,
    RegisteredDateRelatedParticipantList, RegisteredDateParticipantDetail, RegisteredDateParticipantList
)

urlpatterns = [
    path(
        '',
        RegisteredDateActivityListView.as_view(),
        name='registered-date-list'
    ),
    path(
        '/<int:pk>',
        RegisteredDateActivityDetailView.as_view(),
        name='registered-date-detail'
    ),
    path(
        '/transitions',
        RegisteredDateTransitionList.as_view(),
        name='registered-date-transition-list'
    ),

    path(
        '/<int:activity_id>/participants',
        RegisteredDateRelatedParticipantList.as_view(),
        name='registered-date-participants'
    ),
    path(
        '/participants',
        RegisteredDateParticipantList.as_view(),
        name='registered-date-participant-create'
    ),

    path(
        '/participants/transitions',
        RegisteredDateParticipantTransitionList.as_view(),
        name='registered-date-participant-transitions'
    ),
    path(
        '/participants/<int:pk>',
        RegisteredDateParticipantDetail.as_view(),
        name='registered-date-participant-detail'
    ),

    re_path(
        r'^/export/(?P<pk>[\d]+)$',
        RegisteredDateParticipantExportView.as_view(),
        name='registered-date-participant-export'
    ),
]
