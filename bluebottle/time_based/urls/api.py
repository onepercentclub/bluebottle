from django.conf.urls import url

from bluebottle.time_based.views import (
    DateActivityListView, PeriodActivityListView,
    DateActivityDetailView, PeriodActivityDetailView,
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

    url(r'^/applications/on-a-date$',
        DateParticipantList.as_view(),
        name='on-a-date-application-list'),
    url(r'^/applications/on-a-date/(?P<pk>\d+)$',
        DateParticipantDetail.as_view(),
        name='on-a-date-application-detail'),
    url(r'^/applications/on-a-date/transitions$',
        DateParticipantTransitionList.as_view(),
        name='on-a-date-application-transition-list'),
    url(r'^/applications/on-a-date/(?P<pk>\d+)/document$',
        DateParticipantDocumentDetail.as_view(),
        name='on-a-date-application-document'),

    url(r'^/applications/period$',
        PeriodParticipantList.as_view(),
        name='period-application-list'),
    url(r'^/applications/period/(?P<pk>\d+)$',
        PeriodParticipantDetail.as_view(),
        name='period-application-detail'),
    url(r'^/applications/period/transitions$',
        PeriodParticipantTransitionList.as_view(),
        name='period-application-transition-list'),
    url(r'^/applications/period/(?P<pk>\d+)/document$',
        PeriodParticipantDocumentDetail.as_view(),
        name='period-application-document')
]
