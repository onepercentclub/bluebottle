from django.conf.urls import url

from bluebottle.collect.views import (
    CollectContributorExportView, CollectContributorTransitionList,
    CollectContributorDetail, CollectContributorList,
    CollectActivityRelatedCollectContributorList,
    CollectActivityTransitionList, CollectActivityDetailView, CollectActivityListView,
)


urlpatterns = [
    url(r'^$',
        CollectActivityListView.as_view(),
        name='collect-activity-list'),

    url(r'^/(?P<pk>\d+)$',
        CollectActivityDetailView.as_view(),
        name='deed-detail'),

    url(r'^/transitions$',
        CollectActivityTransitionList.as_view(),
        name='collect-activity-transition-list'),

    url(r'^/(?P<activity_id>\d+)/contributors$',
        CollectActivityRelatedCollectContributorList.as_view(),
        name='related-collect-activity-contributors'),

    url(r'^/contributors$',
        CollectContributorList.as_view(),
        name='collect-activity-contributor-list'),
    url(r'^/contributors/(?P<pk>\d+)$',
        CollectContributorDetail.as_view(),
        name='collect-activity-participant-detail'),
    url(r'^/contributors/transitions$',
        CollectContributorTransitionList.as_view(),
        name='collect-activity-contributor-transition-list'),

    url(r'^/export/(?P<pk>[\d]+)$',
        CollectContributorExportView.as_view(),
        name='collect-activity-contributor-export'),
]
