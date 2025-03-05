from django.urls import re_path

from bluebottle.activities.views import (
    ActivityLocationList, ActivityPreviewList, ActivityDetail, ActivityTransitionList,
    RelatedActivityImageList,
    RelatedActivityImageContent, ActivityImage,
    InviteDetailView, ContributionList, ActivityList
)

urlpatterns = [
    re_path(
        r'^/transitions$',
        ActivityTransitionList.as_view(),
        name='activity-transition-list'),

    re_path(
        r'^/search$',
        ActivityPreviewList.as_view(),
        name='activity-preview-list'
    ),

    re_path(
        r'^/contributions$',
        ContributionList.as_view(),
        name='contribution-list'
    ),

    re_path(
        r'^/(?P<pk>\d+)$',
        ActivityDetail.as_view(),
        name='activity-detail'
    ),

    re_path(
        r'^/$',
        ActivityList.as_view(),
        name='activity-list'
    ),

    re_path(
        r'^/(?P<pk>\d+)/image/(?P<size>\d+(x\d+)?)$',
        ActivityImage.as_view(),
        name='activity-image'
    ),

    re_path(
        r'^/related-images$',
        RelatedActivityImageList.as_view(),
        name='related-activity-image-list'
    ),
    re_path(
        r'^/(?P<pk>\d+)/related-image/(?P<size>\d+(x\d+)?)$',
        RelatedActivityImageContent.as_view(),
        name='related-activity-image-content'
    ),

    re_path(
        r'^/invites/(?P<pk>[\w\-]+)/$',
        InviteDetailView.as_view(),
        name='invite-detail'
    ),

    re_path(
        r'^/locations/$',
        ActivityLocationList.as_view(),
        name='activity-location-list'
    ),
]
