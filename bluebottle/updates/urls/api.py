from django.urls import path
from django.urls import re_path

from bluebottle.updates.views import UpdateList, UpdateDetail, ActivityUpdateList, UpdateImageContent, UpdateImageList

urlpatterns = [
    path('', UpdateList.as_view(), name='update-list'),
    path('activity/<int:activity_pk>', ActivityUpdateList.as_view(), name='activity-update-list'),
    path('<int:pk>', UpdateDetail.as_view(), name='update-detail'),
    path('images/', UpdateImageList.as_view(), name='update-image-list'),


    re_path(
        r'^(?P<pk>\d+)/image/(?P<size>\d+(x\d+)?)$',
        UpdateImageContent.as_view(),
        name='update-image'
    ),
]
