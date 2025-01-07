from django.urls import re_path

from bluebottle.funding_flutterwave.views import FlutterwavePaymentList, FlutterwaveWebhookView, \
    FlutterwaveBankAccountAccountList, FlutterwaveBankAccountAccountDetail

urlpatterns = [
    re_path(r'^/payments/$',
        FlutterwavePaymentList.as_view(),
        name='flutterwave-payment-list'),
    re_path(r'^/webhook/$',
        FlutterwaveWebhookView.as_view(),
        name='flutterwave-payment-webhook'),
    re_path(r'^/bank-accounts/$',
        FlutterwaveBankAccountAccountList.as_view(),
        name='flutterwave-external-account-list'),
    re_path(r'^/bank-accounts/(?P<pk>[\d]+)$',
        FlutterwaveBankAccountAccountDetail.as_view(),
        name='flutterwave-external-account-detail'),
]
