from django.urls import re_path

from bluebottle.activity_pub.views import (
    PersonView, InboxView, OutBoxView, PublicKeyView, FollowView,
    AcceptView, PublishView, AnnounceView, OrganizationView,
    GoodDeedView, ImageView, CrowdFundingView, PlaceView, AddressView,
    DoGoodEventView, SubEventView
)

app_name = 'activity_pub'

urlpatterns = [
    re_path(r'^person/(?P<pk>\d+)$', PersonView.as_view(), name='person'),
    re_path(r'^inbox/(?P<pk>\d+)$', InboxView.as_view(), name='inbox'),
    re_path(r'^outbox/(?P<pk>\d+)$', OutBoxView.as_view(), name='outbox'),
    re_path(r'^publickey/(?P<pk>\d+)$', PublicKeyView.as_view(), name='public-key'),
    re_path(r'^follow/(?P<pk>\d+)$', FollowView.as_view(), name='follow'),
    re_path(r'^accept/(?P<pk>\d+)$', AcceptView.as_view(), name='accept'),
    re_path(r'^image/(?P<pk>\d+)$', ImageView.as_view(), name='image'),
    re_path(r'^place/(?P<pk>\d+)$', PlaceView.as_view(), name='place'),
    re_path(r'^address/(?P<pk>\d+)$', AddressView.as_view(), name='address'),
    re_path(r'^good-deed/(?P<pk>\d+)$', GoodDeedView.as_view(), name='good-deed'),
    re_path(r'^crowd-funding/(?P<pk>\d+)$', CrowdFundingView.as_view(), name='crowd-funding'),
    re_path(r'^do-good-event/(?P<pk>\d+)$', DoGoodEventView.as_view(), name='do-good-event'),
    re_path(r'^sub-event/(?P<pk>\d+)$', SubEventView.as_view(), name='sub-event'),
    re_path(r'^publish/(?P<pk>\d+)$', PublishView.as_view(), name='publish'),
    re_path(r'^announce/(?P<pk>\d+)$', AnnounceView.as_view(), name='announce'),
    re_path(r'^organization/(?P<pk>\d+)$', OrganizationView.as_view(), name='organization'),
]
