from django.conf import settings
from django.conf.urls import patterns, url

from ..views import TagList, TagSearch


urlpatterns = patterns(
    '',
    url(r'^tags/$', TagList.as_view(), name='utils_tag_list'),
    url(r'^tags/(?P<search>[-\w]+)$', TagSearch.as_view(), name='utils_tag_list'),

)

INCLUDE_TEST_MODELS = getattr(settings, 'INCLUDE_TEST_MODELS', False)

if INCLUDE_TEST_MODELS:
    from ..views import MetaDataDetail

    urlpatterns += patterns(
        '',
        # metadata testing
        url(r'^metadata/(?P<pk>\d+)$', MetaDataDetail.as_view(), name='meta_test'),
    )
