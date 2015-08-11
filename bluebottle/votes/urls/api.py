from django.conf.urls import patterns, url

from ..views import ProjectVoteList

urlpatterns = patterns(
    '',
    url(r'^projects/(?P<project_id>[\d]+)$', ProjectVoteList.as_view(),
        name='project_votes_list'),
)
