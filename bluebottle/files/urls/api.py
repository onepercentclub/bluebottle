from django.conf.urls import url

from bluebottle.files.views import FileList, ImageList, PrivateFileList, ImageDetail, ImagePreview

urlpatterns = [
    url(r'^documents$', FileList.as_view(), name='document-list'),
    url(r'^private-documents$', PrivateFileList.as_view(), name='private-document-list'),
    url(r'^images$', ImageList.as_view(), name='image-list'),
    url(r'^images/(?P<pk>[\w\-]*)$', ImageDetail.as_view(), name='image-detail'),
    url(r'^images/(?P<pk>.*)/preview$', ImagePreview.as_view(), name='upload-image-preview'),
]
