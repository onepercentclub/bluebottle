from django.conf.urls import url

from bluebottle.time_based.views import (
    OnADateActivityListView, WithADeadlineActivityListView, OngoingActivityListView,
    OnADateActivityDetailView, WithADeadlineActivityDetailView, OngoingActivityDetailView,
    OnADateTransitionList, WithADeadlineTransitionList, OngoingTransitionList,
    OnADateApplicationList, OnADateApplicationDetail,
    OnADateApplicationTransitionList, OnADateApplicationDocumentDetail,
    OnADateActivityIcalView,

    PeriodApplicationList, PeriodApplicationDetail,
    PeriodApplicationTransitionList, PeriodApplicationDocumentDetail
)

urlpatterns = [
    # Events
    url(r'^/on-a-date$',
        OnADateActivityListView.as_view(),
        name='on-a-date-list'),

    url(r'^/with-a-deadline$',
        WithADeadlineActivityListView.as_view(),
        name='with-a-deadline-list'),

    url(r'^/ongoing$',
        OngoingActivityListView.as_view(),
        name='ongoing-list'),

    url(r'^/on-a-date/(?P<pk>\d+)$',
        OnADateActivityDetailView.as_view(),
        name='on-a-date-detail'),

    url(r'^/on-a-date/ical/(?P<pk>\d+)$',
        OnADateActivityIcalView.as_view(),
        name='on-a-date-ical'),

    url(r'^/with-a-deadline/(?P<pk>\d+)$',
        WithADeadlineActivityDetailView.as_view(),
        name='with-a-deadline-detail'),

    url(r'^/ongoing/(?P<pk>\d+)$',
        OngoingActivityDetailView.as_view(),
        name='ongoing-detail'),


    url(r'^/on-a-date/transitions$',
        OnADateTransitionList.as_view(),
        name='on-a-date-transition-list'),

    url(r'^/with-a-deadline/transitions$',
        WithADeadlineTransitionList.as_view(),
        name='with-a-deadline-transition-list'),

    url(r'^/ongoing/transitions$',
        OngoingTransitionList.as_view(),
        name='ongoing-transition-list'),


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
