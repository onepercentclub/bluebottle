from django.conf.urls import url

from bluebottle.initiatives.views import (
    InitiativeList, InitiativeDetail, InitiativeImage,
    InitiativeReviewTransitionList, InitiativeValidation
)


urlpatterns = [
    url(
        r'^/transitions$',
        InitiativeReviewTransitionList.as_view(),
        name='initiative-review-transition-list'
    ),
    url(r'^$', InitiativeList.as_view(), name='initiative-list'),
    url(r'^/(?P<pk>\d+)$', InitiativeDetail.as_view(), name='initiative-detail'),
    url(r'^/validations/(?P<pk>\d+)$', InitiativeValidation.as_view(), name='initiative-validations'),
    url(
        r'^/(?P<pk>\d+)/image/(?P<size>\d+x\d+)$',
        InitiativeImage.as_view(),
        name='initiative-image'
    )
]
