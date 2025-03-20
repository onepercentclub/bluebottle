from django.urls import re_path

from bluebottle.time_based.views import (
    PeriodicTransitionList,
    PeriodicActivityListView, PeriodicActivityDetailView,
    PeriodicRelatedRegistrationList, PeriodicRegistrationList, PeriodicRegistrationTransitionList,
    PeriodicRegistrationDetail,
    PeriodicRegistrationDocumentDetail, PeriodicParticipantTransitionList, PeriodicParticipantExportView,
    PeriodicRelatedParticipantList, PeriodicParticipantDetail
)

urlpatterns = [
    re_path(
        r'^$',
        PeriodicActivityListView.as_view(),
        name='periodic-list'
    ),
    re_path(
        r'^/(?P<pk>\d+)$',
        PeriodicActivityDetailView.as_view(),
        name='periodic-detail'
    ),
    re_path(
        r'^/transitions$',
        PeriodicTransitionList.as_view(),
        name='periodic-transition-list'
    ),

    re_path(
        r'^/(?P<activity_id>\d+)/registrations/$',
        PeriodicRelatedRegistrationList.as_view(),
        name='related-periodic-registrations'
    ),
    re_path(
        r'^/registrations/$',
        PeriodicRegistrationList.as_view(),
        name='periodic-registration-list'
    ),
    re_path(
        r'^/registrations/transitions$',
        PeriodicRegistrationTransitionList.as_view(),
        name='periodic-registration-transitions'
    ),
    re_path(
        r'^/registrations/(?P<pk>\d+)$',
        PeriodicRegistrationDetail.as_view(),
        name='periodic-registration-detail'
    ),
    re_path(
        r'^/registrations/(?P<pk>\d+)/document$',
        PeriodicRegistrationDocumentDetail.as_view(),
        name='periodic-registration-document'
    ),

    re_path(
        r'^/(?P<activity_id>\d+)/participants$',
        PeriodicRelatedParticipantList.as_view(),
        name='periodic-participants'
    ),
    re_path(
        r'^/participants/transitions$',
        PeriodicParticipantTransitionList.as_view(),
        name='periodic-participant-transitions'
    ),
    re_path(
        r'^/participants/(?P<pk>\d+)$',
        PeriodicParticipantDetail.as_view(),
        name='periodic-participant-detail'
    ),

    re_path(
        r'^/export/(?P<pk>[\d]+)$',
        PeriodicParticipantExportView.as_view(),
        name='periodic-participant-export'
    ),
]
