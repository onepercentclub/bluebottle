from django.urls import re_path

from ..views import NewsItemPreviewList, NewsItemList, NewsItemDetail

urlpatterns = [
    # News Items
    re_path(r'^preview-items/$', NewsItemPreviewList.as_view(),
        name='news_preview_list'),
    re_path(r'^items/$', NewsItemList.as_view(), name='news_item_list'),
    re_path(r'^items/(?P<slug>[-\w]+)$', NewsItemDetail.as_view(),
        name='news_post_detail'),
]
