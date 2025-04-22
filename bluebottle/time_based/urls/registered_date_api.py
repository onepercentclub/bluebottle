from django.urls import re_path

from bluebottle.time_based.views import (
    RegisteredDateTransitionList,
    RegisteredDateActivityListView, RegisteredDateActivityDetailView,
    RegisteredDateParticipantTransitionList, RegisteredDateParticipantExportView,
    RegisteredDateRelatedParticipantList, RegisteredDateParticipantDetail, RegisteredDateParticipantList
)

urlpatterns = [
    re_path(
        r'^$',
        RegisteredDateActivityListView.as_view(),
        name='registered-date-list'
    ),
    re_path(
        r'^/(?P<pk>\d+)$',
        RegisteredDateActivityDetailView.as_view(),
        name='registered-date-detail'
    ),
    re_path(
        r'^/transitions$',
        RegisteredDateTransitionList.as_view(),
        name='registered-date-transition-list'
    ),

    re_path(
        r'^/(?P<activity_id>\d+)/participants$',
        RegisteredDateRelatedParticipantList.as_view(),
        name='registered-date-participants'
    ),
    re_path(
        r'^/participants$',
        RegisteredDateParticipantList.as_view(),
        name='registered-date-participant-create'
    ),

    re_path(
        r'^/participants/transitions$',
        RegisteredDateParticipantTransitionList.as_view(),
        name='registered-date-participant-transitions'
    ),
    re_path(
        r'^/participants/(?P<pk>\d+)$',
        RegisteredDateParticipantDetail.as_view(),
        name='registered-date-participant-detail'
    ),

    re_path(
        r'^/export/(?P<pk>[\d]+)$',
        RegisteredDateParticipantExportView.as_view(),
        name='registered-date-participant-export'
    ),
]
