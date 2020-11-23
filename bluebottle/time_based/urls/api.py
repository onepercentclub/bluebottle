from django.conf.urls import url

from bluebottle.time_based.views import (
    DateActivityListView, PeriodActivityListView,
    DateActivityDetailView, PeriodActivityDetailView,
    DateActivityRelatedParticipantList, PeriodActivityRelatedParticipantList,
    DateTransitionList, PeriodTransitionList,
    DateParticipantList, DateParticipantDetail,
    DateParticipantTransitionList, DateParticipantDocumentDetail,
    DateActivityIcalView,

    PeriodParticipantList, PeriodParticipantDetail,
    PeriodParticipantTransitionList, PeriodParticipantDocumentDetail
)

urlpatterns = [
    # Events
    url(r'^/date$',
        DateActivityListView.as_view(),
        name='date-list'),

    url(r'^/period$',
        PeriodActivityListView.as_view(),
        name='period-list'),

    url(r'^/date/(?P<pk>\d+)$',
        DateActivityDetailView.as_view(),
        name='date-detail'),

    url(r'^/date/(?P<activity_id>\d+)/participants$',
        DateActivityRelatedParticipantList.as_view(),
        name='date-participants'),

    url(r'^/date/ical/(?P<pk>\d+)$',
        DateActivityIcalView.as_view(),
        name='date-ical'),

    url(r'^/period/(?P<pk>\d+)$',
        PeriodActivityDetailView.as_view(),
        name='period-detail'),

    url(r'^/period/(?P<activity_id>\d+)/participants$',
        PeriodActivityRelatedParticipantList.as_view(),
        name='period-participants'),

    url(r'^/date/ical/(?P<pk>\d+)$',
        DateActivityIcalView.as_view(),
        name='date-ical'),

    url(r'^/period/(?P<pk>\d+)$',
        PeriodActivityDetailView.as_view(),
        name='period-detail'),

    url(r'^/date/transitions$',
        DateTransitionList.as_view(),
        name='date-transition-list'),

    url(r'^/period/transitions$',
        PeriodTransitionList.as_view(),
        name='period-transition-list'),

    url(r'^/participants/date$',
        DateParticipantList.as_view(),
        name='date-participant-list'),
    url(r'^/participants/date/(?P<pk>\d+)$',
        DateParticipantDetail.as_view(),
        name='date-participant-detail'),
    url(r'^/participants/date/transitions$',
        DateParticipantTransitionList.as_view(),
        name='date-participant-transition-list'),
    url(r'^/participants/date/(?P<pk>\d+)/document$',
        DateParticipantDocumentDetail.as_view(),
        name='date-participant-document'),

    url(r'^/participants/period$',
        PeriodParticipantList.as_view(),
        name='period-participant-list'),
    url(r'^/participants/period/(?P<pk>\d+)$',
        PeriodParticipantDetail.as_view(),
        name='period-participant-detail'),
    url(r'^/participants/period/transitions$',
        PeriodParticipantTransitionList.as_view(),
        name='period-participant-transition-list'),
    url(r'^/participants/period/(?P<pk>\d+)/document$',
        PeriodParticipantDocumentDetail.as_view(),
        name='period-participant-document')
]
