from django.conf.urls import url

from bluebottle.time_based.views import (
    OnADateActivityListView, WithADeadlineActivityListView, OngoingActivityListView,
    OnADateActivityDetailView, WithADeadlineActivityDetailView, OngoingActivityDetailView,
    OnADateTransitionList, WithADeadlineTransitionList, OngoingTransitionList
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
]
