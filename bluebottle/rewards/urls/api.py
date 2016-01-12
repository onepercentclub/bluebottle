from django.conf.urls import patterns, url

from ..views import ProjectRewardList, ProjectRewardDetail

urlpatterns = patterns(
    '',
    url(r'^projects/(?P<project_slug>[\w-]+)/$', ProjectRewardList.as_view(),
        name='project-reward-list'),
    url(r'^projects/(?P<project_slug>[\w-]+)/(?P<pk>[\d]+)$', ProjectRewardDetail.as_view(),
        name='project-reward-detail'),

)
