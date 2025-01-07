from django.urls import re_path

from bluebottle.initiatives.views import (
    InitiativeList, InitiativeDetail, InitiativeImage,
    RelatedInitiativeImageList, RelatedInitiativeImageContent,
    InitiativeReviewTransitionList,
    InitiativeMapList, InitiativePreviewList, InitiativeRedirectList,
    ThemeList, ThemeDetail
)


urlpatterns = [

    re_path(
        r'^$',
        InitiativeList.as_view(),
        name='initiative-list'
    ),
    re_path(
        r'^/(?P<pk>\d+)$',
        InitiativeDetail.as_view(),
        name='initiative-detail'
    ),
    re_path(
        r'^/transitions$',
        InitiativeReviewTransitionList.as_view(),
        name='initiative-review-transition-list'
    ),
    re_path(
        r'^/(?P<pk>\d+)/image/(?P<size>\d+x\d+)$',
        InitiativeImage.as_view(),
        name='initiative-image'
    ),

    re_path(
        r'^/redirects$',
        InitiativeRedirectList.as_view(),
        name='initiative-redirect-list'
    ),

    re_path(
        r'^/related-images$',
        RelatedInitiativeImageList.as_view(),
        name='related-initiative-image-list'
    ),
    re_path(
        r'^/themes$',
        ThemeList.as_view(),
        name='initiative-theme-list'
    ),
    re_path(
        r'^/themes/(?P<pk>\d+)$',
        ThemeDetail.as_view(),
        name='initiative-theme'
    ),

    re_path(
        r'^/(?P<pk>\d+)/related-image/(?P<size>\d+(x\d+)?)$',
        RelatedInitiativeImageContent.as_view(),
        name='related-initiative-image-content'
    ),

    re_path(
        r'^/map/$',
        InitiativeMapList.as_view(),
        name='initiative-map-list'
    ),
    re_path(
        r'^/preview/$',
        InitiativePreviewList.as_view(),
        name='initiative-preview-list'
    ),
]
