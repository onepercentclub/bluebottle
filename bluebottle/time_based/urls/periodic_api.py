from django.urls import path
from django.urls import re_path

from bluebottle.time_based.views import (
    PeriodicTransitionList,
    PeriodicActivityListView, PeriodicActivityDetailView,
    PeriodicRelatedRegistrationList, PeriodicRegistrationList, PeriodicRegistrationTransitionList,
    PeriodicRegistrationDetail,
    PeriodicParticipantTransitionList, PeriodicParticipantExportView,
    PeriodicRelatedParticipantList, PeriodicParticipantDetail
)

urlpatterns = [
    path(
        '',
        PeriodicActivityListView.as_view(),
        name='periodic-list'
    ),
    path(
        '/<int:pk>',
        PeriodicActivityDetailView.as_view(),
        name='periodic-detail'
    ),
    path(
        '/transitions',
        PeriodicTransitionList.as_view(),
        name='periodic-transition-list'
    ),

    path(
        '/<int:activity_id>/registrations/',
        PeriodicRelatedRegistrationList.as_view(),
        name='related-periodic-registrations'
    ),
    path(
        '/registrations/',
        PeriodicRegistrationList.as_view(),
        name='periodic-registration-list'
    ),
    path(
        '/registrations/transitions',
        PeriodicRegistrationTransitionList.as_view(),
        name='periodic-registration-transitions'
    ),
    path(
        '/registrations/<int:pk>',
        PeriodicRegistrationDetail.as_view(),
        name='periodic-registration-detail'
    ),

    path(
        '/<int:activity_id>/participants',
        PeriodicRelatedParticipantList.as_view(),
        name='periodic-participants'
    ),
    path(
        '/participants/transitions',
        PeriodicParticipantTransitionList.as_view(),
        name='periodic-participant-transitions'
    ),
    path(
        '/participants/<int:pk>',
        PeriodicParticipantDetail.as_view(),
        name='periodic-participant-detail'
    ),

    re_path(
        r'^/export/(?P<pk>[\d]+)$',
        PeriodicParticipantExportView.as_view(),
        name='periodic-participant-export'
    ),
]
