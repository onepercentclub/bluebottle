from django.urls import path
from django.urls import re_path

from bluebottle.collect.views import (
    CollectContributorExportView, CollectContributorTransitionList,
    CollectContributorDetail, CollectContributorList,
    CollectActivityRelatedCollectContributorList,
    CollectActivityTransitionList, CollectActivityDetailView, CollectActivityListView, CollectTypeList,
    CollectTypeDetail, CollectIcalView,
)


urlpatterns = [
    path(
        '',
        CollectActivityListView.as_view(),
        name='collect-activity-list'
    ),

    path(
        '/<int:pk>',
        CollectActivityDetailView.as_view(),
        name='collect-activity-detail'
    ),

    path(
        '/transitions',
        CollectActivityTransitionList.as_view(),
        name='collect-activity-transition-list'
    ),

    path(
        '/<int:activity_id>/contributors',
        CollectActivityRelatedCollectContributorList.as_view(),
        name='related-collect-contributors'
    ),

    path(
        '/contributors',
        CollectContributorList.as_view(),
        name='collect-contributor-list'
    ),
    path(
        '/contributors/<int:pk>',
        CollectContributorDetail.as_view(),
        name='collect-contributor-detail'
    ),
    path(
        '/contributors/transitions',
        CollectContributorTransitionList.as_view(),
        name='collect-contributor-transition-list'
    ),

    re_path(
        r'^/export/(?P<pk>[\d]+)$',
        CollectContributorExportView.as_view(),
        name='collect-contributors-export'
    ),

    path(
        '/types/',
        CollectTypeList.as_view(),
        name='collect-type-list'
    ),
    path(
        '/types/<int:pk>',
        CollectTypeDetail.as_view(),
        name='collect-type-detail'
    ),

    path(
        '/ical/<int:pk>',
        CollectIcalView.as_view(),
        name='collect-ical'
    ),

]
