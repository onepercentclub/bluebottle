from django.conf.urls import patterns, url
from surlex.dj import surl

from .views import TagList, TagSearch  # ,ThemeList 


urlpatterns = patterns('',
    #url(r'^themes/$', ThemeList.as_view(), name='utils-theme-list'),
    url(r'^tags/$', TagList.as_view(), name='utils-tag-list'),
    surl(r'^tags/<search:s>$', TagSearch.as_view(), name='utils-tag-list')
)
