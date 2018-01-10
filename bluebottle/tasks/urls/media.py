from django.conf.urls import url

from bluebottle.tasks.views import TaskMemberResumeView


urlpatterns = [
    url(r'^taskmember/resume/(?P<pk>\d+)',
        TaskMemberResumeView.as_view(),
        name='task-member-resume'),
]
