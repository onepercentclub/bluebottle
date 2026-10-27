from django.urls import path

from bluebottle.activity_pub.views import (
    PersonView, InboxView, OutBoxView, PublicKeyView, FollowView,
    AcceptView, CreateView, OrganizationView,
    GoodDeedView, ImageView, CrowdFundingView, CollectCampaignView, PlaceView, AddressView,
    GrantApplicationView,
    DoGoodEventView, SubEventView, UpdateView,
    DeleteView, StartView, CancelView, FinishView
)

app_name = 'activity_pub'

urlpatterns = [
    path('person/<int:pk>', PersonView.as_view(), name='person'),
    path('inbox/<int:pk>', InboxView.as_view(), name='inbox'),
    path('outbox/<int:pk>', OutBoxView.as_view(), name='outbox'),
    path('publickey/<int:pk>', PublicKeyView.as_view(), name='public-key'),
    path('follow/<int:pk>', FollowView.as_view(), name='follow'),
    path('accept/<int:pk>', AcceptView.as_view(), name='accept'),
    path('image/<int:pk>', ImageView.as_view(), name='image'),
    path('place/<int:pk>', PlaceView.as_view(), name='place'),
    path('address/<int:pk>', AddressView.as_view(), name='address'),
    path('good-deed/<int:pk>', GoodDeedView.as_view(), name='good-deed'),
    path('crowd-funding/<int:pk>', CrowdFundingView.as_view(), name='crowd-funding'),
    path('grant-application/<int:pk>', GrantApplicationView.as_view(), name='grant-application'),
    path('collect-campaign/<int:pk>', CollectCampaignView.as_view(), name='collect-campaign'),
    path('do-good-event/<int:pk>', DoGoodEventView.as_view(), name='do-good-event'),
    path('sub-event/<int:pk>', SubEventView.as_view(), name='sub-event'),
    path('create/<int:pk>', CreateView.as_view(), name='create'),
    path('update/<int:pk>', UpdateView.as_view(), name='update'),
    path('delete/<int:pk>', DeleteView.as_view(), name='delete'),
    path('cancel/<int:pk>', CancelView.as_view(), name='cancel'),
    path('start/<int:pk>', StartView.as_view(), name='start'),
    path('finish/<int:pk>', FinishView.as_view(), name='finish'),
    path('organization/<int:pk>', OrganizationView.as_view(), name='organization'),
]
