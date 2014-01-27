from django.conf.urls import patterns, url

from ..views import HomePageDetail

urlpatterns = patterns(
    '',
    url(r'^(?P<language>[-\w]+)$', HomePageDetail.as_view(), name='stats'),
)
