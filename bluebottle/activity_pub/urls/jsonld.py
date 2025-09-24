from django.urls import re_path

from bluebottle.activity_pub.views import (
    PersonView, InboxView, OutBoxView, PublicKeyView, FollowView,
    AcceptView, EventView, PublishView, AnnounceView, OrganizationView, PlaceView
)

app_name = 'activity_pub'

urlpatterns = [
    re_path(r'^person/(?P<pk>\d+)$', PersonView.as_view(), name='person'),
    re_path(r'^inbox/(?P<pk>\d+)$', InboxView.as_view(), name='inbox'),
    re_path(r'^outbox/(?P<pk>\d+)$', OutBoxView.as_view(), name='outbox'),
    re_path(r'^publickey/(?P<pk>\d+)$', PublicKeyView.as_view(), name='public-key'),
    re_path(r'^follow/(?P<pk>\d+)$', FollowView.as_view(), name='follow'),
    re_path(r'^accept/(?P<pk>\d+)$', AcceptView.as_view(), name='accept'),
    re_path(r'^event/(?P<pk>\d+)$', EventView.as_view(), name='event'),
    re_path(r'^publish/(?P<pk>\d+)$', PublishView.as_view(), name='publish'),
    re_path(r'^announce/(?P<pk>\d+)$', AnnounceView.as_view(), name='announce'),
    re_path(r'^organization/(?P<pk>\d+)$', OrganizationView.as_view(), name='organization'),
    re_path(r'^place/(?P<pk>\d+)$', PlaceView.as_view(), name='place'),
]
