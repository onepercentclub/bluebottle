from django.conf.urls import url

from bluebottle.funding_flutterwave.views import FlutterwavePaymentList, FlutterwaveWebhookView


urlpatterns = [
    url(r'^$', FlutterwavePaymentList.as_view(), name='flutterwave-payment-list'),
    url(r'^webhook$', FlutterwaveWebhookView.as_view(), name='flutterwave-payment-webhook'),
]
