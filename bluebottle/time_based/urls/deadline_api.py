from django.urls import path
from django.urls import re_path

from bluebottle.time_based.views import (
    DeadlineTransitionList,
    DeadlineActivityListView, DeadlineActivityDetailView,
    DeadlineRelatedRegistrationList, DeadlineRegistrationList, DeadlineRegistrationTransitionList,
    DeadlineRegistrationDetail,
    DeadlineParticipantTransitionList, DeadlineParticipantExportView,
    DeadlineRelatedParticipantList, DeadlineParticipantDetail, DeadlineParticipantList
)

urlpatterns = [
    path(
        '',
        DeadlineActivityListView.as_view(),
        name='deadline-list'
    ),
    path(
        '/<int:pk>',
        DeadlineActivityDetailView.as_view(),
        name='deadline-detail'
    ),
    path(
        '/transitions',
        DeadlineTransitionList.as_view(),
        name='deadline-transition-list'
    ),

    path(
        '/<int:activity_id>/registrations/',
        DeadlineRelatedRegistrationList.as_view(),
        name='related-deadline-registrations'
    ),
    path(
        '/registrations/',
        DeadlineRegistrationList.as_view(),
        name='deadline-registration-list'
    ),
    path(
        '/registrations/transitions',
        DeadlineRegistrationTransitionList.as_view(),
        name='deadline-registration-transitions'),
    path(
        '/registrations/<int:pk>',
        DeadlineRegistrationDetail.as_view(),
        name='deadline-registration-detail'
    ),

    path(
        '/<int:activity_id>/participants',
        DeadlineRelatedParticipantList.as_view(),
        name='deadline-participants'
    ),
    path(
        '/participants',
        DeadlineParticipantList.as_view(),
        name='deadline-participant-create'
    ),

    path(
        '/participants/transitions',
        DeadlineParticipantTransitionList.as_view(),
        name='deadline-participant-transitions'
    ),
    path(
        '/participants/<int:pk>',
        DeadlineParticipantDetail.as_view(),
        name='deadline-participant-detail'
    ),

    re_path(
        r'^/export/(?P<pk>[\d]+)$',
        DeadlineParticipantExportView.as_view(),
        name='deadline-participant-export'
    ),
]
