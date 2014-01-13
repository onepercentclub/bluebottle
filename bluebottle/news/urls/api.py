from django.conf.urls import patterns, url
from surlex.dj import surl
from ..views import NewsItemPreviewList, NewsItemList, NewsItemDetail

urlpatterns = patterns('',

    # News Items
    url(r'^preview-items/$', NewsItemPreviewList.as_view(), name='news-preview-list'),
    url(r'^items/$', NewsItemList.as_view(), name='news-item-list'),
    surl(r'^items/<slug:s>$', NewsItemDetail.as_view(), name='news-post-detail'),

)
