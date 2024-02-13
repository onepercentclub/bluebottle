from django.conf.urls import url

from bluebottle.time_based.views import (
    DeadlineTransitionList,
    DeadlineActivityListView, DeadlineActivityDetailView,
    DeadlineRelatedRegistrationList, DeadlineRegistrationList, DeadlineRegistrationTransitionList,
    DeadlineRegistrationDetail,
    DeadlineRegistrationDocumentDetail, DeadlineParticipantTransitionList, DeadlineParticipantExportView,
    DeadlineRelatedParticipantList, DeadlineParticipantDetail
)

urlpatterns = [
    url(r'^$',
        DeadlineActivityListView.as_view(),
        name='deadline-list'),
    url(r'^/(?P<pk>\d+)$',
        DeadlineActivityDetailView.as_view(),
        name='deadline-detail'),
    url(r'^/transitions$',
        DeadlineTransitionList.as_view(),
        name='deadline-transition-list'),

    url(r'^/(?P<activity_id>\d+)/registrations/$',
        DeadlineRelatedRegistrationList.as_view(),
        name='related-deadline-registrations'),
    url(r'^/registrations/$',
        DeadlineRegistrationList.as_view(),
        name='deadline-registration-list'),
    url(r'^/registrations/transitions$',
        DeadlineRegistrationTransitionList.as_view(),
        name='deadline-registration-transitions'),
    url(r'^/registrations/(?P<activity_id>\d+)$',
        DeadlineRegistrationDetail.as_view(),
        name='deadline-registration-detail'),
    url(r'^/registrations/(?P<pk>\d+)/document$',
        DeadlineRegistrationDocumentDetail.as_view(),
        name='deadline-registration-document'),

    url(r'^/(?P<activity_id>\d+)/participants$',
        DeadlineRelatedParticipantList.as_view(),
        name='deadline-participants'),
    url(r'^/participants/transitions$',
        DeadlineParticipantTransitionList.as_view(),
        name='deadline-participant-transitions'),

    url(r'^/participants/(?P<activity_id>\d+)$',
        DeadlineParticipantDetail.as_view(),
        name='deadline-participant-detail'),

    url(r'^/export/(?P<pk>[\d]+)$',
        DeadlineParticipantExportView.as_view(),
        name='deadline-participant-export'),
]
