from django.conf.urls import patterns, url

from ..views import PaymentResponseView

urlpatterns = patterns(
    '',
    url(r'^payment_response/(?P<order_payment_id>\d+)$',
        PaymentResponseView.as_view(),
        name='interswitch-payment-response'),
)
