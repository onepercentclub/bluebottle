from django.conf.urls import patterns, url

from ..views import SlideList

urlpatterns = patterns(
    '',
    url(r'^$', SlideList.as_view(), name='slide_list'),
)
