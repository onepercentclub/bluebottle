from django.conf.urls import url

from bluebottle.bluebottle_dashboard.views import AnalyticsView

urlpatterns = [
    url(r'^$', AnalyticsView.as_view(), name='analytics-index'),
]
