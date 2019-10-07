from django.conf.urls import url

from bluebottle.funding_flutterwave.views import FlutterwavePaymentList, FlutterwaveWebhookView, \
    FlutterwaveBankAccountAccountList, FlutterwaveBankAccountAccountDetail

urlpatterns = [
    url(r'^/payments/$',
        FlutterwavePaymentList.as_view(),
        name='flutterwave-payment-list'),
    url(r'^/webhook/$',
        FlutterwaveWebhookView.as_view(),
        name='flutterwave-payment-webhook'),
    url(r'^/bank-accounts/$',
        FlutterwaveBankAccountAccountList.as_view(),
        name='flutterwave-external-account-list'),
    url(r'^/bank-accounts/(?P<pk>[\d]+)$',
        FlutterwaveBankAccountAccountDetail.as_view(),
        name='flutterwave-external-account-detail'),
]
