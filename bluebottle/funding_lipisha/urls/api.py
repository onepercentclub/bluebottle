from django.urls import path
from django.urls import re_path

from bluebottle.funding_lipisha.views import (
    LipishaPaymentList, LipishaWebHookView,
    LipishaBankAccountAccountDetail,
    LipishaBankAccountAccountList)

urlpatterns = [
    path(
        '/payments/',
        LipishaPaymentList.as_view(),
        name='lipisha-payment-list'
    ),
    path(
        '/webhook/',
        LipishaWebHookView.as_view(),
        name='lipisha-payment-webhook'
    ),
    path(
        '/bank-accounts/',
        LipishaBankAccountAccountList.as_view(),
        name='lipisha-external-account-list'
    ),
    re_path(
        r'^/bank-accounts/(?P<pk>[\d]+)$',
        LipishaBankAccountAccountDetail.as_view(),
        name='lipisha-external-account-detail'
    ),
]
