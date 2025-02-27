from django.urls import re_path

from bluebottle.files.views import FileList, ImageList, PrivateFileList, PrivateFileDetail, ImagePreview, ImageDetail

urlpatterns = [
    re_path(r'^documents$', FileList.as_view(), name='document-list'),
    re_path(r'^private-documents$', PrivateFileList.as_view(), name='private-document-list'),
    re_path(r'^private-documents/(?P<pk>[\w\-]*)$', PrivateFileDetail.as_view(), name='private-document-detail'),
    re_path(r'^images$', ImageList.as_view(), name='image-list'),
    re_path(r'^images/(?P<pk>[\w\-]*)$', ImageDetail.as_view(), name='image-detail'),
    re_path(r'^images/(?P<pk>.*)/(?P<size>\d+(x\d+)?)$', ImagePreview.as_view(), name='upload-image-preview'),
]
