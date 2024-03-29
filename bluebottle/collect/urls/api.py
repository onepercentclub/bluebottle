from django.conf.urls import url

from bluebottle.collect.views import (
    CollectContributorExportView, CollectContributorTransitionList,
    CollectContributorDetail, CollectContributorList,
    CollectActivityRelatedCollectContributorList,
    CollectActivityTransitionList, CollectActivityDetailView, CollectActivityListView, CollectTypeList,
    CollectTypeDetail, CollectIcalView,
)


urlpatterns = [
    url(r'^$',
        CollectActivityListView.as_view(),
        name='collect-activity-list'),

    url(r'^/(?P<pk>\d+)$',
        CollectActivityDetailView.as_view(),
        name='collect-activity-detail'),

    url(r'^/transitions$',
        CollectActivityTransitionList.as_view(),
        name='collect-activity-transition-list'),

    url(r'^/(?P<activity_id>\d+)/contributors$',
        CollectActivityRelatedCollectContributorList.as_view(),
        name='related-collect-contributors'),

    url(r'^/contributors$',
        CollectContributorList.as_view(),
        name='collect-contributor-list'),
    url(r'^/contributors/(?P<pk>\d+)$',
        CollectContributorDetail.as_view(),
        name='collect-contributor-detail'),
    url(r'^/contributors/transitions$',
        CollectContributorTransitionList.as_view(),
        name='collect-contributor-transition-list'),

    url(r'^/export/(?P<pk>[\d]+)$',
        CollectContributorExportView.as_view(),
        name='collect-contributors-export'),

    url(
        r'^/types/$',
        CollectTypeList.as_view(),
        name='collect-type-list'
    ),
    url(
        r'^/types/(?P<pk>\d+)$',
        CollectTypeDetail.as_view(),
        name='collect-type-detail'
    ),

    url(r'^/ical/(?P<pk>\d+)$',
        CollectIcalView.as_view(),
        name='collect-ical'),

]
