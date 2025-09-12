from django.urls import re_path

from bluebottle.activities.views import (
    ActivityLocationList, ActivityPreviewList, ActivityDetail, ActivityTransitionList,
    RelatedActivityImageList,
    RelatedActivityImageContent, ActivityImage,
    InviteDetailView, ContributionList, ActivityList,
    ActivityQuestionList, ActivityAnswerList, ActivityAnswerDetail,
    FileUploadAnswerDocumentView, ActivityQrCode
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
        r'^/(?P<pk>\d+)/qr-code',
        ActivityQrCode.as_view(),
        name='activity-qr-code'
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

    re_path(
        r'^/questions/(?P<type>[\w\-]+)/$',
        ActivityQuestionList.as_view(),
        name='activity-question-list'
    ),

    re_path(
        r'^/answers/$',
        ActivityAnswerList.as_view(),
        name='activity-answer-list'
    ),

    re_path(
        r'^/answers/(?P<pk>\d+)$',
        ActivityAnswerDetail.as_view(),
        name='activity-answer-detail'
    ),

    re_path(
        r'^/answers/(?P<pk>\d+)/document/(?P<type>.+)/$',
        FileUploadAnswerDocumentView.as_view(),
        name='file-upload-answer-document'
    ),
]
