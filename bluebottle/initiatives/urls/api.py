from django.urls import path
from django.urls import re_path

from bluebottle.initiatives.views import (
    InitiativeList, InitiativeDetail, InitiativeImage,
    RelatedInitiativeImageList, RelatedInitiativeImageContent,
    InitiativeReviewTransitionList,
    InitiativeMapList, InitiativePreviewList, InitiativeRedirectList,
    ThemeList, ThemeDetail
)


urlpatterns = [

    path(
        '',
        InitiativeList.as_view(),
        name='initiative-list'
    ),
    path(
        '/<int:pk>',
        InitiativeDetail.as_view(),
        name='initiative-detail'
    ),
    path(
        '/transitions',
        InitiativeReviewTransitionList.as_view(),
        name='initiative-review-transition-list'
    ),
    re_path(
        r'^/(?P<pk>\d+)/image/(?P<size>\d+(x\d+)?)$',
        InitiativeImage.as_view(),
        name='initiative-image'
    ),

    path(
        '/redirects',
        InitiativeRedirectList.as_view(),
        name='initiative-redirect-list'
    ),

    path(
        '/related-images',
        RelatedInitiativeImageList.as_view(),
        name='related-initiative-image-list'
    ),
    path(
        '/themes',
        ThemeList.as_view(),
        name='initiative-theme-list'
    ),
    path(
        '/themes/<int:pk>',
        ThemeDetail.as_view(),
        name='initiative-theme'
    ),

    re_path(
        r'^/(?P<pk>\d+)/related-image/(?P<size>\d+(x\d+)?)$',
        RelatedInitiativeImageContent.as_view(),
        name='related-initiative-image-content'
    ),

    path(
        '/map/',
        InitiativeMapList.as_view(),
        name='initiative-map-list'
    ),
    path(
        '/preview/',
        InitiativePreviewList.as_view(),
        name='initiative-preview-list'
    ),
]
