from django.urls import re_path

from bluebottle.activity_pub.views import (
    JSONLDView, InboxView,
)

app_name = 'activity_pub'

urlpatterns = [
    re_path(r'^inbox/(?P<pk>\d+)$', InboxView.as_view(), name='inbox'),
    re_path(r'^(?P<type>.+)/(?P<pk>\d+)$', JSONLDView.as_view(), name='resource'),
]
