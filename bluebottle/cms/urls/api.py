from django.conf.urls import url

from bluebottle.cms.views import (
    NewsItemDetail, NewsItemList, PageDetail, BlockDetail, HomeDetail
)

urlpatterns = [

    url(r'^home$', HomeDetail.as_view(), {'pk': 1}, name='home-detail'),
    url(r'^blocks/(?P<pk>\d+)$', BlockDetail.as_view(), name='page-block-detail'),

    url(r'^(?P<slug>[\w-]+)$', PageDetail.as_view(), name='page-detail'),
    url(r'^(?P<slug>[\w-]+)$', NewsItemDetail.as_view(), name='page-detail'),
    url(r'^(?P<slug>[\w-]+)$', NewsItemList.as_view(), name='page-detail'),
]
