from django.conf.urls import patterns, url
from ..views import StatusChangedNotificationView

urlpatterns = patterns('',
    url(r'^$', StatusChangedNotificationView.as_view(), name='payment-logger-status-changed'),
)
