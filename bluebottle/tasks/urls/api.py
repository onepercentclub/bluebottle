from django.conf.urls import patterns, url, include
from surlex.dj import surl
from ..views import (TaskDetail, TaskList, TaskWallPostList, TaskWallPostDetail, TaskMemberList, TaskMemberDetail,
                    TaskFileList, TaskFileDetail, TaskPreviewList, SkillList, MyTaskMemberList)


urlpatterns = patterns('',

    url(r'^$', TaskList.as_view(), name='task-list'),
    surl(r'^<pk:#>$', TaskDetail.as_view(), name='task-detail'),

    url(r'^previews/$', TaskPreviewList.as_view(), name='task-preview-list'),

    url(r'^skills/$', SkillList.as_view(), name='task-skill-list'),

    # Task Members
    url(r'^members/$', TaskMemberList.as_view(), name='task-member-list'),
    surl(r'^members/<pk:#>$', TaskMemberDetail.as_view(), name='task-member-detail'),
    url(r'^members/my-tasks/$', MyTaskMemberList.as_view(), name='my-task-member-list'),

    # Task Files
    url(r'^files/$', TaskFileList.as_view(), name='task-member-list'),
    surl(r'^files/<pk:#>$', TaskFileDetail.as_view(), name='task-member-detail'),

    # Task WallPost Urls
    surl(r'^wallposts/$', TaskWallPostList.as_view(), name='task-wallpost-list'),
    surl(r'^wallposts/<pk:#>$', TaskWallPostDetail.as_view(), name='task-wallpost-detail'),
)
