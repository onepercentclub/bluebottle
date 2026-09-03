from django.urls import path

from bluebottle.projects.views import ProjectImageCreate

urlpatterns = [
    path(
        'project-images/',
        ProjectImageCreate.as_view(),
        name='project-image-create'
    ),
]
