from django.conf.urls import url
from ..views import TagList, TagSearch, LanguageList
from ..views import ShareFlyer

urlpatterns = [
    url(r'^languages/$', LanguageList.as_view(), name='utils_language_list'),
    url(r'^tags/$', TagList.as_view(), name='utils_tag_list'),
    url(r'^tags/(?P<search>[-\w]+)$', TagSearch.as_view(),
        name='utils_tag_list'),
    url(r'^share_flyer/$', ShareFlyer.as_view(), name="share_flyer"),
]
