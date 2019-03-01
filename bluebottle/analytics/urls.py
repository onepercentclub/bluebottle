from django.contrib import admin
from django.conf.urls import url

from bluebottle.analytics.views import ReportDownloadView, ReportExportView

urlpatterns = [
    url(r'^report-export/$',
        admin.site.admin_view(ReportExportView.as_view()),
        name='report-export'),
    url(r'^report-download/$',
        admin.site.admin_view(ReportDownloadView.as_view()),
        name='report-download')
]
