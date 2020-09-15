from django.conf.urls import url

from bluebottle.projects.views import ProjectImageCreate

urlpatterns = [
    url(r'^project-images/$',
        ProjectImageCreate.as_view(),
        name='project-image-create'),
]
