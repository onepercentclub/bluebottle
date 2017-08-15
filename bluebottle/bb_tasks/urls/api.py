from django.conf.urls import url

from ..views import (
    TaskDetail, TaskList, TaskMemberList, TaskMemberDetail,
    TaskFileList, TaskFileDetail, MyTaskList, MyTaskDetail,
    TaskPreviewList, MyTaskMemberList, SkillList, UsedSkillList)

urlpatterns = [
    url(r'^$', TaskList.as_view(), name='task-list'),
    url(r'^(?P<pk>\d+)$', TaskDetail.as_view(), name='task_detail'),
    url(r'^my/$', MyTaskList.as_view(), name='my_task_list'),
    url(r'^my/(?P<pk>\d+)$', MyTaskDetail.as_view(), name='my_task_detail'),

    url(r'^previews/$', TaskPreviewList.as_view(), name='task_preview_list'),

    url(r'^skills/$', SkillList.as_view(), name='task_skill_list'),
    url(r'^used_skills/$', UsedSkillList.as_view(), name='used_task_skill_list'),

    # Task Members
    url(r'^members/$', TaskMemberList.as_view(), name='task-member-list'),
    url(r'^members/(?P<pk>\d+)$', TaskMemberDetail.as_view(), name='task-member-detail'),
    url(r'^members/my-tasks/$', MyTaskMemberList.as_view(), name='my_task_member_list'),

    # Task Files
    url(r'^files/$', TaskFileList.as_view(), name='task_file_list'),
    url(r'^files/(?P<pk>\d+)$', TaskFileDetail.as_view(), name='task_file_detail'),
]
