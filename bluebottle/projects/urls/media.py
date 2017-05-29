from django.conf.urls import url

from bluebottle.projects.views import ProjectDocumentFileView


urlpatterns = [
    url(r'^project/documents/(?P<pk>\d+)',
        ProjectDocumentFileView.as_view(),
        name='project-document-file'),
]
