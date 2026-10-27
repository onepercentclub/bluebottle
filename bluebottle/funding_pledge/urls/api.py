from django.urls import path
from django.urls import re_path

from bluebottle.funding_pledge.views import PledgePaymentList, PledgeBankAccountAccountList, \
    PledgeBankAccountAccountDetail

urlpatterns = [
    path(
        '',
        PledgePaymentList.as_view(),
        name='pledge-payment-list'
    ),
    path(
        '/bank-accounts/',
        PledgeBankAccountAccountList.as_view(),
        name='pledge-external-account-list'
    ),
    re_path(
        r'^/bank-accounts/(?P<pk>[\d]+)$',
        PledgeBankAccountAccountDetail.as_view(),
        name='pledge-external-account-detail'
    ),
]
