from django.conf.urls import url

from bluebottle.files.views import FileList, ImageList, PrivateFileList, ImageDetail

urlpatterns = [
    url(r'^documents$', FileList.as_view(), name='document-list'),
    url(r'^private-documents$', PrivateFileList.as_view(), name='private-document-list'),
    url(r'^images$', ImageList.as_view(), name='image-list'),
    url(r'^images/(?P<pk>.*)$', ImageDetail.as_view(), name='image-detail'),
]
