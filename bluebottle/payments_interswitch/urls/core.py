from django.conf.urls import url

from ..views import PaymentResponseView, PaymentStatusListener

urlpatterns = [
    url(r'^status_update/$',
        PaymentStatusListener.as_view(),
        name='interswitch-status-update'),
    url(r'^payment_response/(?P<order_payment_id>\d+)$',
        PaymentResponseView.as_view(),
        name='interswitch-payment-reposponse'),
]
