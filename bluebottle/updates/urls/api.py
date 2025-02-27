from django.urls import re_path

from bluebottle.updates.views import UpdateList, UpdateDetail, ActivityUpdateList, UpdateImageContent, UpdateImageList

urlpatterns = [
    re_path(r'^$', UpdateList.as_view(), name='update-list'),
    re_path(r'^activity/(?P<activity_pk>\d+)$', ActivityUpdateList.as_view(), name='activity-update-list'),
    re_path(r'^(?P<pk>\d+)$', UpdateDetail.as_view(), name='update-detail'),
    re_path(r'^images/$', UpdateImageList.as_view(), name='update-image-list'),


    re_path(
        r'^(?P<pk>\d+)/image/(?P<size>\d+x\d+)$',
        UpdateImageContent.as_view(),
        name='update-image'
    ),
]
