from django.conf.urls import patterns, url

from ..views import (
    TaskDetail, TaskList, TaskWallPostList, TaskWallPostDetail, TaskMemberList,
    TaskMemberDetail, TaskFileList, TaskFileDetail, TaskPreviewList, SkillList,
    MyTaskMemberList)


urlpatterns = patterns(
    '',
    url(r'^$', TaskList.as_view(), name='task_list'),
    url(r'^(?P<pk>\d+)$', TaskDetail.as_view(), name='task_detail'),

    url(r'^previews/$', TaskPreviewList.as_view(), name='task_preview_list'),

    url(r'^skills/$', SkillList.as_view(), name='task_skill_list'),

    # Task Members
    url(r'^members/$', TaskMemberList.as_view(), name='task_member_list'),
    url(r'^members/(?P<pk>\d+)$', TaskMemberDetail.as_view(), name='task_member_detail'),
    url(r'^members/my-tasks/$', MyTaskMemberList.as_view(), name='my_task_member_list'),

    # Task Files
    url(r'^files/$', TaskFileList.as_view(), name='task_member_list'),
    url(r'^files/(?P<pk>\d+)$', TaskFileDetail.as_view(), name='task_member_detail'),

    # Task WallPost Urls
    url(r'^wallposts/$', TaskWallPostList.as_view(), name='task_wallpost_list'),
    url(r'^wallposts/(?P<pk>\d+)$', TaskWallPostDetail.as_view(), name='task_wallpost_detail'),
)
