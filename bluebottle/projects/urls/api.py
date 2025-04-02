from django.urls import re_path

from bluebottle.projects.views import ProjectImageCreate

urlpatterns = [
    re_path(
        r'^project-images/$',
        ProjectImageCreate.as_view(),
        name='project-image-create'
    ),
]
