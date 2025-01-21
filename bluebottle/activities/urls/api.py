from django.conf.urls import url

from bluebottle.activities.views import (
    ActivityLocationList, ActivityPreviewList, ActivityDetail, ActivityTransitionList,
    RelatedActivityImageList,
    RelatedActivityImageContent, ActivityImage,
    InviteDetailView, ContributionList, ActivityList
)

urlpatterns = [
    url(
        r'^/transitions$',
        ActivityTransitionList.as_view(),
        name='activity-transition-list'),

    url(r'^/search$',
        ActivityPreviewList.as_view(),
        name='activity-preview-list'),

    url(r'^/contributions$',
        ContributionList.as_view(),
        name='contribution-list'),

    url(r'^/(?P<pk>\d+)$',
        ActivityDetail.as_view(),
        name='activity-detail'),

    url(r'^/$',
        ActivityList.as_view(),
        name='activity-list'),

    url(
        r'^/(?P<pk>\d+)/image/(?P<size>\d+(x\d+)?)$',
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

    url(
        r'^/invites/(?P<pk>[\w\-]+)/$',
        InviteDetailView.as_view(),
        name='invite-detail'
    ),

    url(
        r'^/locations/$',
        ActivityLocationList.as_view(),
        name='activity-location-list'
    ),
]
