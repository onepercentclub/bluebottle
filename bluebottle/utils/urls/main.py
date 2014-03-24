from django.conf.urls import patterns, url

from ..views import DocumentDownloadView

urlpatterns = patterns(
    '',
    url(r'^(?P<content_type>\d+)/(?P<pk>\d+)$', DocumentDownloadView.as_view(), name='document_download_detail'),
)
