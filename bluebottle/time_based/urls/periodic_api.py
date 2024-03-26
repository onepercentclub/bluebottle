from django.conf.urls import url

from bluebottle.time_based.views import (
    PeriodicTransitionList,
    PeriodicActivityListView, PeriodicActivityDetailView,
    PeriodicRelatedRegistrationList, PeriodicRegistrationList, PeriodicRegistrationTransitionList,
    PeriodicRegistrationDetail,
    PeriodicRegistrationDocumentDetail, PeriodicParticipantTransitionList, PeriodicParticipantExportView,
    PeriodicRelatedParticipantList, PeriodicParticipantDetail
)

urlpatterns = [
    url(r'^$',
        PeriodicActivityListView.as_view(),
        name='periodic-list'),
    url(r'^/(?P<pk>\d+)$',
        PeriodicActivityDetailView.as_view(),
        name='periodic-detail'),
    url(r'^/transitions$',
        PeriodicTransitionList.as_view(),
        name='periodic-transition-list'),

    url(r'^/(?P<activity_id>\d+)/registrations/$',
        PeriodicRelatedRegistrationList.as_view(),
        name='related-periodic-registrations'),
    url(r'^/registrations/$',
        PeriodicRegistrationList.as_view(),
        name='periodic-registration-list'),
    url(r'^/registrations/transitions$',
        PeriodicRegistrationTransitionList.as_view(),
        name='periodic-registration-transitions'),
    url(r'^/registrations/(?P<pk>\d+)$',
        PeriodicRegistrationDetail.as_view(),
        name='periodic-registration-detail'),
    url(r'^/registrations/(?P<pk>\d+)/document$',
        PeriodicRegistrationDocumentDetail.as_view(),
        name='periodic-registration-document'),

    url(r'^/(?P<activity_id>\d+)/participants$',
        PeriodicRelatedParticipantList.as_view(),
        name='periodic-participants'),
    url(r'^/participants/transitions$',
        PeriodicParticipantTransitionList.as_view(),
        name='periodic-participant-transitions'),
    url(r'^/participants/(?P<pk>\d+)$',
        PeriodicParticipantDetail.as_view(),
        name='periodic-participant-detail'),

    url(r'^/export/(?P<pk>[\d]+)$',
        PeriodicParticipantExportView.as_view(),
        name='periodic-participant-export'),
]
