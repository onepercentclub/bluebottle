from django.urls import re_path

from bluebottle.cms.views import (
    NewsItemDetail, NewsItemList, PageDetail, BlockDetail, HomeDetail
)

urlpatterns = [

    re_path(r'^home$', HomeDetail.as_view(), {'pk': 1}, name='home-detail'),
    re_path(r'^blocks/(?P<pk>\d+)$', BlockDetail.as_view(), name='page-block-detail'),

    re_path(r'^page/(?P<slug>[\w-]+)$', PageDetail.as_view(), name='page-detail'),

    re_path(r'^news/$', NewsItemList.as_view(), name='news-list'),
    re_path(r'^news/(?P<slug>[\w-]+)$', NewsItemDetail.as_view(), name='news-detail'),
]
