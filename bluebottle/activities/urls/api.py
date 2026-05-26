from django.urls import path
from django.urls import re_path

from bluebottle.activities.views import (
    ActivityLocationList, ActivityPreviewList, ActivityDetailView, ActivityTransitionList,
    RelatedActivityImageList,
    RelatedActivityImageContent, ActivityImage,
    InviteDetailView, ContributionList, ActivityList,
    ActivityQuestionList, ActivityAnswerList, ActivityAnswerDetail,
    FileUploadAnswerDocumentView, ActivityQrCode, ActivityMessageList,
)

urlpatterns = [
    path(
        '/transitions',
        ActivityTransitionList.as_view(),
        name='activity-transition-list'),

    path(
        '/search',
        ActivityPreviewList.as_view(),
        name='activity-preview-list'
    ),

    path(
        '/contributions',
        ContributionList.as_view(),
        name='contribution-list'
    ),

    path(
        '/<int:pk>',
        ActivityDetailView.as_view(),
        name='activity-detail'
    ),

    path(
        '/',
        ActivityList.as_view(),
        name='activity-list'
    ),

    re_path(
        r'^/(?P<pk>\d+)/image/(?P<size>\d+(x\d+)?)$',
        ActivityImage.as_view(),
        name='activity-image'
    ),

    re_path(
        r'^/(?P<pk>\d+)/qr-code',
        ActivityQrCode.as_view(),
        name='activity-qr-code'
    ),

    path(
        '/related-images',
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

    path(
        '/locations/',
        ActivityLocationList.as_view(),
        name='activity-location-list'
    ),

    re_path(
        r'^/questions/(?P<type>[\w\-]+)/$',
        ActivityQuestionList.as_view(),
        name='activity-question-list'
    ),

    re_path(
        r'^/activity-messages/$',
        ActivityMessageList.as_view(),
        name='activity-message-list'
    ),

    re_path(
        r'^/answers/$',
        ActivityAnswerList.as_view(),
        name='activity-answer-list'
    ),

    path(
        '/answers/<int:pk>',
        ActivityAnswerDetail.as_view(),
        name='activity-answer-detail'
    ),

    path(
        '/answers/<int:pk>/document/',
        FileUploadAnswerDocumentView.as_view(),
        name='file-upload-answer-document'
    ),
]
