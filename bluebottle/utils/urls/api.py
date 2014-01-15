from django.conf import settings
from django.conf.urls import patterns, url
from surlex.dj import surl

from ..views import TagList, TagSearch  # ,ThemeList



urlpatterns = patterns('',
    url(r'^tags/$', TagList.as_view(), name='utils-tag-list'),
    surl(r'^tags/<search:s>$', TagSearch.as_view(), name='utils-tag-list'),

)



INCLUDE_TEST_MODELS = getattr(settings, 'INCLUDE_TEST_MODELS', False)

if INCLUDE_TEST_MODELS:
    from ..views import MetaDataDetail

    urlpatterns += patterns('', 
        # metadata testing
        surl(r'^metadata/<pk:#>$', MetaDataDetail.as_view(), name='meta-test'),
    )
