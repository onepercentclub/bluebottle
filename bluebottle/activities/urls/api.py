from django.conf.urls import url

from bluebottle.activities.views import (
    ActivityLocationList, ActivityPreviewList, ActivityDetail, ActivityTransitionList,
    ContributorList, RelatedActivityImageList,
    RelatedActivityImageContent, ActivityImage,
    TeamList, TeamTransitionList, TeamMembersList,
    InviteDetailView, TeamMembersExportView
)

urlpatterns = [
    url(
        r'^/transitions$',
        ActivityTransitionList.as_view(),
        name='activity-transition-list'),
    url(r'^/search$',
        ActivityPreviewList.as_view(),
        name='activity-preview-list'),
    url(r'^/contributors$',
        ContributorList.as_view(),
        name='contributor-list'),

    url(r'^/team/(?P<team_id>\d+)/members$',
        TeamMembersList.as_view(),
        name='team-members'),

    url(r'^/team/(?P<pk>\d+)/members/export$',
        TeamMembersExportView.as_view(),
        name='team-members-export'),

    url(r'^/(?P<pk>\d+)$',
        ActivityDetail.as_view(),
        name='activity-detail'),

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
        r'^/teams/$',
        TeamList.as_view(),
        name='team-list'
    ),

    url(
        r'^/teams/transitions$',
        TeamTransitionList.as_view(),
        name='team-transition-list'),

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
