from django.conf.urls import url

from bluebottle.projects.views import (
    ProjectSupportersExportView
)


urlpatterns = [
    url(r'^project/supporters/(?P<slug>[-\w]+)',
        ProjectSupportersExportView.as_view(),
        name='project-supporters-export'),

]
