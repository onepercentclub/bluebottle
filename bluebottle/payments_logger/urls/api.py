from django.conf.urls import url
from ..views import StatusChangedNotificationView

urlpatterns = [
    url(r'^$', StatusChangedNotificationView.as_view(),
        name='payment-logger-status-changed'),
]
