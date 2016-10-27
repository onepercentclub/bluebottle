from django.conf.urls import url

from ..views import NewsItemPreviewList, NewsItemList, NewsItemDetail

urlpatterns = [
    # News Items
    url(r'^preview-items/$', NewsItemPreviewList.as_view(),
        name='news_preview_list'),
    url(r'^items/$', NewsItemList.as_view(), name='news_item_list'),
    url(r'^items/(?P<slug>[-\w]+)$', NewsItemDetail.as_view(),
        name='news_post_detail'),
]
