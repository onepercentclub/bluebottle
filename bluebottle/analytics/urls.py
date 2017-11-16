from django.contrib import admin
from django.conf.urls import url

from bluebottle.analytics.views import ReportDownloadView
from .views import ParticipationMetricsFormView

urlpatterns = [
    url(r'^participation-metrics/$',
        admin.site.admin_view(ParticipationMetricsFormView.as_view()),
        name='participation-metrics'),
    url(r'^report-download/$',
        admin.site.admin_view(ReportDownloadView.as_view()),
        name='report-download')
]
