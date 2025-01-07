from django.urls import re_path

from bluebottle.collect.views import (
    CollectContributorExportView, CollectContributorTransitionList,
    CollectContributorDetail, CollectContributorList,
    CollectActivityRelatedCollectContributorList,
    CollectActivityTransitionList, CollectActivityDetailView, CollectActivityListView, CollectTypeList,
    CollectTypeDetail, CollectIcalView,
)


urlpatterns = [
    re_path(
        r'^$',
        CollectActivityListView.as_view(),
        name='collect-activity-list'
    ),

    re_path(
        r'^/(?P<pk>\d+)$',
        CollectActivityDetailView.as_view(),
        name='collect-activity-detail'
    ),

    re_path(
        r'^/transitions$',
        CollectActivityTransitionList.as_view(),
        name='collect-activity-transition-list'
    ),

    re_path(
        r'^/(?P<activity_id>\d+)/contributors$',
        CollectActivityRelatedCollectContributorList.as_view(),
        name='related-collect-contributors'
    ),

    re_path(
        r'^/contributors$',
        CollectContributorList.as_view(),
        name='collect-contributor-list'
    ),
    re_path(
        r'^/contributors/(?P<pk>\d+)$',
        CollectContributorDetail.as_view(),
        name='collect-contributor-detail'
    ),
    re_path(
        r'^/contributors/transitions$',
        CollectContributorTransitionList.as_view(),
        name='collect-contributor-transition-list'
    ),

    re_path(
        r'^/export/(?P<pk>[\d]+)$',
        CollectContributorExportView.as_view(),
        name='collect-contributors-export'
    ),

    re_path(
        r'^/types/$',
        CollectTypeList.as_view(),
        name='collect-type-list'
    ),
    re_path(
        r'^/types/(?P<pk>\d+)$',
        CollectTypeDetail.as_view(),
        name='collect-type-detail'
    ),

    re_path(
        r'^/ical/(?P<pk>\d+)$',
        CollectIcalView.as_view(),
        name='collect-ical'
    ),

]
