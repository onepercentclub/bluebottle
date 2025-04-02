from django.urls import re_path

from bluebottle.funding_telesom.views import (
    TelesomPaymentList,
    TelesomBankAccountAccountList,
    TelesomBankAccountAccountDetail)

urlpatterns = [
    re_path(
        r'^/payments/$',
        TelesomPaymentList.as_view(),
        name='telesom-payment-list'
    ),
    re_path(
        r'^/bank-accounts/$',
        TelesomBankAccountAccountList.as_view(),
        name='telesom-external-account-list'
    ),
    re_path(
        r'^/bank-accounts/(?P<pk>[\d]+)$',
        TelesomBankAccountAccountDetail.as_view(),
        name='telesom-external-account-detail'
    ),
]
