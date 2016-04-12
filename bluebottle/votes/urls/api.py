from django.conf.urls import patterns, url

from ..views import VoteList

urlpatterns = patterns(
    '',
    url(r'^$', VoteList.as_view(), name='vote_list'),
)
