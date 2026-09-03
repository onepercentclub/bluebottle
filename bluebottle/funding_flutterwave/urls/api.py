from django.urls import path
from django.urls import re_path

from bluebottle.funding_flutterwave.views import FlutterwavePaymentList, FlutterwaveWebhookView, \
    FlutterwaveBankAccountAccountList, FlutterwaveBankAccountAccountDetail

urlpatterns = [
    path(
        '/payments/',
        FlutterwavePaymentList.as_view(),
        name='flutterwave-payment-list'
    ),
    path(
        '/webhook/',
        FlutterwaveWebhookView.as_view(),
        name='flutterwave-payment-webhook'
    ),
    path(
        '/bank-accounts/',
        FlutterwaveBankAccountAccountList.as_view(),
        name='flutterwave-external-account-list'
    ),
    re_path(
        r'^/bank-accounts/(?P<pk>[\d]+)$',
        FlutterwaveBankAccountAccountDetail.as_view(),
        name='flutterwave-external-account-detail'
    ),
]
