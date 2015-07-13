from django.conf import settings
from django.conf.urls import patterns, url
from ..views import TagList, TagSearch, LanguageList
from ..views import ShareFlyer


urlpatterns = patterns(
    '',
    url(r'^languages/$', LanguageList.as_view(), name='utils_language_list'),
    url(r'^tags/$', TagList.as_view(), name='utils_tag_list'),
    url(r'^tags/(?P<search>[-\w]+)$', TagSearch.as_view(), name='utils_tag_list'),
    url(r'^share_flyer/(?P<slug>[-\w]+)$', ShareFlyer.as_view(), name="share_flyer"),
)

INCLUDE_TEST_MODELS = getattr(settings, 'INCLUDE_TEST_MODELS', False)

if INCLUDE_TEST_MODELS:
    from ..views import MetaDataDetail
    urlpatterns += patterns(
        '',
        # metadata testing
        url(r'^metadata/(?P<pk>\d+)/$', MetaDataDetail.as_view(), name='meta_test'),
    )
