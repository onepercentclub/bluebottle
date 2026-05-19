from django.urls import path

from bluebottle.activity_pub.views import (
    JSONLDView, InboxView,
)

app_name = 'activity_pub'

urlpatterns = [
    path(r'^inbox/(?P<pk>\d+)$', InboxView.as_view(), name='inbox'),
    path(r'^(?P<type>.+)/(?P<pk>\d+)$', JSONLDView.as_view(), name='resource'),
]
