from django.conf.urls import url

from bluebottle.activities.views import (
    ActivityList, ActivityDetail, ActivityTransitionList,
    ContributorList, RelatedActivityImageList,
    RelatedActivityImageContent, ActivityImage
)

urlpatterns = [
    url(
        r'^/transitions$',
        ActivityTransitionList.as_view(),
        name='activity-transition-list'),
    url(r'^$',
        ActivityList.as_view(),
        name='activity-list'),
    url(r'^/contributors$',
        ContributorList.as_view(),
        name='contributor-list'),

    url(r'^/(?P<pk>\d+)$',
        ActivityDetail.as_view(),
        name='activity-detail'),

    url(
        r'^/(?P<pk>\d+)/image/(?P<size>\d+x\d+)$',
        ActivityImage.as_view(),
        name='activity-image'
    ),


    url(r'^/related-images$',
        RelatedActivityImageList.as_view(),
        name='related-activity-image-list'),
    url(
        r'^/(?P<pk>\d+)/related-image/(?P<size>\d+(x\d+)?)$',
        RelatedActivityImageContent.as_view(),
        name='related-activity-image-content'
    ),
]
