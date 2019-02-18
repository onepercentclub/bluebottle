from django.conf.urls import url

from bluebottle.files.views import FileList

urlpatterns = [
    url(r'^$', FileList.as_view(), name='file-list'),
]
