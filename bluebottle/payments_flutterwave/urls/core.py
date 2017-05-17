from django.conf.urls import url

from ..views import PaymentResponseView, MpesaPaymentUpdateView

urlpatterns = [
    url(r'^payment_response/(?P<order_payment_id>\d+)$',
        PaymentResponseView.as_view(),
        name='flutterwave-payment-response'),
    url(r'^mpesa_update/$',
        MpesaPaymentUpdateView.as_view(),
        name='flutterwave-mpesa-payment-update'),
]
