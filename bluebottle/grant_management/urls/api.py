
from django.urls import re_path

from bluebottle.grant_management.views import (
    GrantPayoutDetails,
    GrantApplicationList,
    GrantApplicationDetail,
    GrantApplicationTransitionList
)

urlpatterns = [
    # Grants
    re_path(r'^$', GrantApplicationList.as_view(), name='grant-application-list'),
    re_path(r'^/(?P<pk>[\d]+)$', GrantApplicationDetail.as_view(), name='grant-application-detail'),
    re_path(r'^/transitions$', GrantApplicationTransitionList.as_view(),
            name='grant-application-transition-list'),

    re_path(
        r'^/grant-payouts/(?P<pk>[\d]+)$',
        GrantPayoutDetails.as_view(),
        name='grant-payout-details'
    ),

]
