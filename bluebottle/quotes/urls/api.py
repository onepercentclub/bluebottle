from django.conf.urls import patterns, url

from ..views import ProjectRewardList, ProjectRewardDetail

urlpatterns = patterns(
    '',
    url(r'^(?P<project_slug>[\w-]+)/rewards/$', ProjectRewardList.as_view(),
        name='project-reward-list'),
    url(r'^(?P<project_slug>[\w-]+)/rewards/(?P<id>[\d]+)$', ProjectRewardDetail.as_view(),
        name='project-reward-detail'),

)
