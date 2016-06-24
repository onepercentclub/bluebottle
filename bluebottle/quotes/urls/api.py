from django.conf.urls import patterns, url

from ..views import QuoteList


urlpatterns = patterns(
    '',
    url(r'^$', QuoteList.as_view(), name='quote_list'),
)
