from django.conf.urls import url

from bluebottle.files.views import FileList, ImageList, PrivateFileList, PrivateFileDetail, ImagePreview, ImageDetail

urlpatterns = [
    url(r'^documents$', FileList.as_view(), name='document-list'),
    url(r'^private-documents$', PrivateFileList.as_view(), name='private-document-list'),
    url(r'^private-documents/(?P<pk>[\w\-]*)$', PrivateFileDetail.as_view(), name='private-document-detail'),
    url(r'^images$', ImageList.as_view(), name='image-list'),
    url(r'^images/(?P<pk>[\w\-]*)$', ImageDetail.as_view(), name='image-detail'),
    url(r'^images/(?P<pk>.*)/(?P<size>\d+(x\d+)?)$', ImagePreview.as_view(), name='upload-image-preview'),
]
