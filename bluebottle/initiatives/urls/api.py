from django.conf.urls import url

from bluebottle.initiatives.views import (
    InitiativeList, InitiativeDetail, InitiativeImage,
    InitiativeReviewTransitionList,
    InitiativeMapList, InitiativeRedirectList
)


urlpatterns = [

    url(r'^$',
        InitiativeList.as_view(),
        name='initiative-list'),
    url(r'^/(?P<pk>\d+)$',
        InitiativeDetail.as_view(),
        name='initiative-detail'),
    url(r'^/map/$',
        InitiativeMapList.as_view(),
        name='initiative-map-list'),

    url(r'^/transitions$',
        InitiativeReviewTransitionList.as_view(),
        name='initiative-review-transition-list'),
    url(r'^/(?P<pk>\d+)/image/(?P<size>\d+x\d+)$',
        InitiativeImage.as_view(),
        name='initiative-image'),

    url(r'^/redirects$',
        InitiativeRedirectList.as_view(),
        name='initiative-redirect-list')
]
