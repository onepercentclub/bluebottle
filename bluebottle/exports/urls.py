from django.conf.urls import url

from .views import ExportView, ExportPendingView, ExportDownloadView


urlpatterns = [
    url(r'^$', ExportView.as_view(), name='exportdb_export'),
    url(r'^progress/$', ExportPendingView.as_view(), name='exportdb_progress'),
    url(r'^download/(?P<filename>[\w\-\.]+)$', ExportDownloadView.as_view(), name='exportdb_download')
]
