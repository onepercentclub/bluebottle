from django.urls import re_path

from bluebottle.time_based.views import (
    DeadlineTransitionList,
    DeadlineActivityListView, DeadlineActivityDetailView,
    DeadlineRelatedRegistrationList, DeadlineRegistrationList, DeadlineRegistrationTransitionList,
    DeadlineRegistrationDetail,
    DeadlineRegistrationDocumentDetail, DeadlineParticipantTransitionList, DeadlineParticipantExportView,
    DeadlineRelatedParticipantList, DeadlineParticipantDetail, DeadlineParticipantList
)

urlpatterns = [
    re_path(
        r'^$',
        DeadlineActivityListView.as_view(),
        name='deadline-list'
    ),
    re_path(
        r'^/(?P<pk>\d+)$',
        DeadlineActivityDetailView.as_view(),
        name='deadline-detail'
    ),
    re_path(
        r'^/transitions$',
        DeadlineTransitionList.as_view(),
        name='deadline-transition-list'
    ),

    re_path(
        r'^/(?P<activity_id>\d+)/registrations/$',
        DeadlineRelatedRegistrationList.as_view(),
        name='related-deadline-registrations'
    ),
    re_path(
        r'^/registrations/$',
        DeadlineRegistrationList.as_view(),
        name='deadline-registration-list'
    ),
    re_path(
        r'^/registrations/transitions$',
        DeadlineRegistrationTransitionList.as_view(),
        name='deadline-registration-transitions'),
    re_path(
        r'^/registrations/(?P<pk>\d+)$',
        DeadlineRegistrationDetail.as_view(),
        name='deadline-registration-detail'
    ),
    re_path(
        r'^/registrations/(?P<pk>\d+)/document$',
        DeadlineRegistrationDocumentDetail.as_view(),
        name='deadline-registration-document'
    ),

    re_path(
        r'^/(?P<activity_id>\d+)/participants$',
        DeadlineRelatedParticipantList.as_view(),
        name='deadline-participants'
    ),
    re_path(
        r'^/participants$',
        DeadlineParticipantList.as_view(),
        name='deadline-participant-create'
    ),

    re_path(
        r'^/participants/transitions$',
        DeadlineParticipantTransitionList.as_view(),
        name='deadline-participant-transitions'
    ),
    re_path(
        r'^/participants/(?P<pk>\d+)$',
        DeadlineParticipantDetail.as_view(),
        name='deadline-participant-detail'
    ),

    re_path(
        r'^/export/(?P<pk>[\d]+)$',
        DeadlineParticipantExportView.as_view(),
        name='deadline-participant-export'
    ),
]
