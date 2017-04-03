from django.conf.urls import url

from ..views import PaymentResponseView

urlpatterns = [
    url(r'^payment_response/(?P<order_payment_id>\d+)$',
        PaymentResponseView.as_view(),
        name='telesom-payment-response'),
]
