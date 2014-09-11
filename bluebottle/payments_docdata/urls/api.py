from django.conf.urls import patterns, url
from ..views import DocdataStatusChangedNotificationView

urlpatterns = patterns('',
    url(r'^$', DocdataStatusChangedNotificationView.as_view(), name='payment-docdata-status-changed'),
)
