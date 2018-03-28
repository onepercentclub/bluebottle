from django.conf.urls import url

from bluebottle.projects.views import (
    ProjectDocumentFileView, ProjectSupportersExportView
)


urlpatterns = [
    url(r'^project/documents/(?P<pk>\d+)',
        ProjectDocumentFileView.as_view(),
        name='project-document-file'),
    url(r'^project/supporters/(?P<pk>\d+)',
        ProjectSupportersExportView.as_view(),
        name='project-supporters-export'),

]
