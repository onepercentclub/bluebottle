from django.urls import re_path

from bluebottle.activity_pub.views import (
    FollowCreateView
)

urlpatterns = [
    re_path(r'^follow/$', FollowCreateView.as_view(), name='activity-pub-follow-list'),
]
