from django.conf.urls import url

from bluebottle.cms.views import (
    ResultPageDetail, HomePageDetail, NewsItemDetail, OldPageDetail, PageDetail, HomeDetail, BlockDetail
)

urlpatterns = [
    url(r'^results/(?P<pk>\d+)$', ResultPageDetail.as_view(), name='result-page-detail'),
    url(r'^homepage$', HomePageDetail.as_view(), {'pk': 1}, name='home-page-detail'),
    url(r'^news-item/(?P<slug>[\w-]+)$', NewsItemDetail.as_view(), name='news-item-detail'),
    url(r'^page/(?P<slug>[\w-]+)$', OldPageDetail.as_view(), name='page-detail'),

    url(r'^home$', HomeDetail.as_view(), {'pk': 1}, name='home-page-detail'),
    url(r'^blocks/(?P<pk>\d+)$', BlockDetail.as_view(), name='page-block-detail'),

    url(r'^(?P<slug>[\w-]+)$', PageDetail.as_view(), name='page-detail'),
]
