from django.urls import path
from django.urls import re_path

from bluebottle.funding_telesom.views import (
    TelesomPaymentList,
    TelesomBankAccountAccountList,
    TelesomBankAccountAccountDetail)

urlpatterns = [
    path(
        '/payments/',
        TelesomPaymentList.as_view(),
        name='telesom-payment-list'
    ),
    path(
        '/bank-accounts/',
        TelesomBankAccountAccountList.as_view(),
        name='telesom-external-account-list'
    ),
    re_path(
        r'^/bank-accounts/(?P<pk>[\d]+)$',
        TelesomBankAccountAccountDetail.as_view(),
        name='telesom-external-account-detail'
    ),
]
