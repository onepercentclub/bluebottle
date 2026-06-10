from django.urls import path, re_path

from bluebottle.content.views import (
    ContentBlockCreate,
    ContentBlockDetail,
    ContentPageDetail,
    ContentPageList,
)

urlpatterns = [
    path('pages', ContentPageList.as_view(), name='content-page-list'),
    re_path(
        r'^pages/(?P<slug>[\w-]+)/blocks/?$',
        ContentBlockCreate.as_view(),
        name='content-block-create',
    ),
    re_path(
        r'^pages/(?P<slug>[\w-]+)$',
        ContentPageDetail.as_view(),
        name='content-page-detail',
    ),
    path('blocks/<int:pk>', ContentBlockDetail.as_view(), name='content-block-detail'),
]
