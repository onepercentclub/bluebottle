from django.conf.urls import url

from bluebottle.time_based.views import (
    DateActivityListView, PeriodActivityListView,
    DateActivityDetailView, PeriodActivityDetailView,
    DateTransitionList, PeriodTransitionList,
    OnADateApplicationList, OnADateApplicationDetail,
    OnADateApplicationTransitionList, OnADateApplicationDocumentDetail,
    DateActivityIcalView,

    PeriodApplicationList, PeriodApplicationDetail,
    PeriodApplicationTransitionList, PeriodApplicationDocumentDetail
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
        OnADateApplicationList.as_view(),
        name='on-a-date-application-list'),
    url(r'^/applications/on-a-date/(?P<pk>\d+)$',
        OnADateApplicationDetail.as_view(),
        name='on-a-date-application-detail'),
    url(r'^/applications/on-a-date/transitions$',
        OnADateApplicationTransitionList.as_view(),
        name='on-a-date-application-transition-list'),
    url(r'^/applications/on-a-date/(?P<pk>\d+)/document$',
        OnADateApplicationDocumentDetail.as_view(),
        name='on-a-date-application-document'),

    url(r'^/applications/period$',
        PeriodApplicationList.as_view(),
        name='period-application-list'),
    url(r'^/applications/period/(?P<pk>\d+)$',
        PeriodApplicationDetail.as_view(),
        name='period-application-detail'),
    url(r'^/applications/period/transitions$',
        PeriodApplicationTransitionList.as_view(),
        name='period-application-transition-list'),
    url(r'^/applications/period/(?P<pk>\d+)/document$',
        PeriodApplicationDocumentDetail.as_view(),
        name='period-application-document')
]
