from django.conf.urls import patterns, url
from surlex.dj import surl

from .views import TagList, TagSearch, MetaDataDetail  # ,ThemeList 


urlpatterns = patterns('',
    url(r'^tags/$', TagList.as_view(), name='utils-tag-list'),
    surl(r'^tags/<search:s>$', TagSearch.as_view(), name='utils-tag-list'),

    # metadata testing
    surl(r'^metadata/<pk:#>$', MetaDataDetail.as_view()),
)
