from django.urls import re_path

from bluebottle.activity_pub.views import (
    PersonView, InboxView, OutBoxView, PublicKeyView, FollowView
)

urlpatterns = [
    re_path(r'^person/(?P<pk>\d+)$', PersonView.as_view(), name='Person'),
    re_path(r'^inbox/(?P<pk>\d+)$', InboxView.as_view(), name='Inbox'),
    re_path(r'^outbox/(?P<pk>\d+)$', OutBoxView.as_view(), name='Outbox'),
    re_path(r'^publickey/(?P<pk>\d+)$', PublicKeyView.as_view(), name='PublicKey'),
    re_path(r'^follow/(?P<pk>\d+)$', FollowView.as_view(), name='Follow'),
]
