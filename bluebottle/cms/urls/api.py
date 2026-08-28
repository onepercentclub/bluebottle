from django.urls import path
from django.urls import re_path

from bluebottle.cms.views import (
    NewsItemDetail, NewsItemList, PageDetail, PageList, BlockDetail, PageBlockCreate,
    HomeDetail, PlatformPageDetail
)

urlpatterns = [

    path('home', HomeDetail.as_view(), {'pk': 1}, name='home-detail'),
    path('blocks/<int:pk>', BlockDetail.as_view(), name='page-block-detail'),

    path('pages', PageList.as_view(), name='page-list'),
    re_path(r'^page/(?P<slug>[\w-]+)/blocks/?$', PageBlockCreate.as_view(), name='page-block-create'),
    re_path(r'^page/(?P<slug>[\w-]+)$', PageDetail.as_view(), name='page-detail'),
    re_path(r'^platform/(?P<slug>[\w-]+)$', PlatformPageDetail.as_view(), name='platform-page-detail'),

    path('news/', NewsItemList.as_view(), name='news-list'),
    re_path(r'^news/(?P<slug>[\w-]+)$', NewsItemDetail.as_view(), name='news-detail'),
]
