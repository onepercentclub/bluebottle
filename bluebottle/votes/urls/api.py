from django.conf.urls import patterns, url
from bluebottle.votes.views import VoteList

from ..views import ProjectVoteList

urlpatterns = patterns(
    '',
    url(r'^projects/(?P<project_id>[\d]+)$', ProjectVoteList.as_view(),
        name='project_votes_list'),
    url(r'^$', VoteList.as_view(), name='vote_list'),
)
