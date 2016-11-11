from django.conf.urls import url

from ..views import DocumentDownloadView

urlpatterns = [
    url(r'^(?P<content_type>\d+)/(?P<pk>\d+)$', DocumentDownloadView.as_view(),
        name='document_download_detail'),
]
