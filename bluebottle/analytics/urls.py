from django.contrib import admin
from django.conf.urls import url

from .views import ParticipationMetricsFormView

urlpatterns = [
    url(r'^participation-metrics/$',
        admin.site.admin_view(ParticipationMetricsFormView.as_view()),
        name='participation-metrics')
]
