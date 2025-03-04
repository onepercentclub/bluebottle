from django.urls import re_path
from ..views import TagList, TagSearch, LanguageList

urlpatterns = [
    re_path(r'^languages/$', LanguageList.as_view(), name='utils_language_list'),
    re_path(r'^tags/$', TagList.as_view(), name='utils_tag_list'),
    re_path(
        r'^tags/(?P<search>[-\w]+)$',
        TagSearch.as_view(),
        name='utils_tag_list'
    ),
]
