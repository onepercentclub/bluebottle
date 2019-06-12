from django.conf.urls import url

from bluebottle.files.views import FileList, ImageList

urlpatterns = [
    url(r'^documents$', FileList.as_view(), name='document-list'),
    url(r'^images$', ImageList.as_view(), name='image-list'),
]
