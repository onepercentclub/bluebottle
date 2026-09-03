from django.urls import path
from django.urls import re_path

from ..views import NewsItemPreviewList, NewsItemList, NewsItemDetail

urlpatterns = [
    # News Items
    path(
        'preview-items/',
        NewsItemPreviewList.as_view(),
        name='news_preview_list'
    ),
    path('items/', NewsItemList.as_view(), name='news_item_list'),
    re_path(
        r'^items/(?P<slug>[-\w]+)$',
        NewsItemDetail.as_view(),
        name='news_post_detail'
    ),
]
