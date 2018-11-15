from django.conf.urls import url

from ..views import PaymentStatusUpdateView

urlpatterns = [
    url(r'^status_update/(?P<merchant_order_id>[\d-]+)$',
        PaymentStatusUpdateView.as_view(),
        name='stripe-payment-status-update'),
]
