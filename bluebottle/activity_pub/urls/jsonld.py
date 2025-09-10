from django.urls import re_path

from bluebottle.activity_pub.views import (
    PersonView, InboxView, OutBoxView, PublicKeyView, FollowView,
    AcceptView
)

app_name = 'activity_pub'

urlpatterns = [
    re_path(r'^person/(?P<pk>\d+)$', PersonView.as_view(), name='person'),
    re_path(r'^inbox/(?P<pk>\d+)$', InboxView.as_view(), name='inbox'),
    re_path(r'^outbox/(?P<pk>\d+)$', OutBoxView.as_view(), name='outbox'),
    re_path(r'^publickey/(?P<pk>\d+)$', PublicKeyView.as_view(), name='public-key'),
    re_path(r'^follow/(?P<pk>\d+)$', FollowView.as_view(), name='follow'),
    re_path(r'^accept/(?P<pk>\d+)$', AcceptView.as_view(), name='accept'),
]
