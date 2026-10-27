
from django.urls import path
from django.urls import re_path

from bluebottle.grant_management.views import (
    GrantPayoutDetails,
    GrantApplicationList,
    GrantApplicationDetail,
    GrantApplicationTransitionList
)

urlpatterns = [
    # Grants
    path('', GrantApplicationList.as_view(), name='grant-application-list'),
    re_path(r'^/(?P<pk>[\d]+)$', GrantApplicationDetail.as_view(), name='grant-application-detail'),
    path(
        '/transitions', GrantApplicationTransitionList.as_view(),
        name='grant-application-transition-list'
    ),

    re_path(
        r'^/grant-payouts/(?P<pk>[\d]+)$',
        GrantPayoutDetails.as_view(),
        name='grant-payout-details'
    ),

]
