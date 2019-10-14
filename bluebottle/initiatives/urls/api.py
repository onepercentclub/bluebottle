from django.conf.urls import url

from bluebottle.initiatives.views import (
    InitiativeList, InitiativeDetail, InitiativeImage,
    RelatedInitiativeImageList, RelatedInitiativeImageContent,
    InitiativeReviewTransitionList,
    InitiativeMapList)


urlpatterns = [

    url(
        r'^$',
        InitiativeList.as_view(),
        name='initiative-list'
    ),
    url(
        r'^/(?P<pk>\d+)$',
        InitiativeDetail.as_view(),
        name='initiative-detail'
    ),
    url(
        r'^/transitions$',
        InitiativeReviewTransitionList.as_view(),
        name='initiative-review-transition-list'
    ),
    url(
        r'^/(?P<pk>\d+)/image/(?P<size>\d+x\d+)$',
        InitiativeImage.as_view(),
        name='initiative-image'
    ),

    url(
        r'^/related-image$',
        RelatedInitiativeImageList.as_view(),
        name='related-initiative-image-list'),
    url(
        r'^/(?P<pk>\d+)/related-image/(?P<size>\d+(x\d+)?)$',
        RelatedInitiativeImageContent.as_view(),
        name='related-initiative-image-content'
    ),

    url(
        r'^/map/$',
        InitiativeMapList.as_view(),
        name='initiative-map-list'
    ),

]
