from django.conf.urls import url

from bluebottle.payments_flutterwave.views import FlutterwaveWebhookView, PaymentResponseView

urlpatterns = [
    url(r'^payment_response/(?P<order_payment_id>\d+)$',
        PaymentResponseView.as_view(),
        name='flutterwave-payment-response'),
    url(r'^webhook$',
        FlutterwaveWebhookView.as_view(),
        name='flutterwave-webhook'),
]
