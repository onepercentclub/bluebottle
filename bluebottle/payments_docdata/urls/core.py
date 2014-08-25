from django.conf.urls import patterns, url

from ..views import PaymentStatusUpdateView


urlpatterns = patterns(
    '',
    url(r'^status_update/(?P<payment_cluster_id>[\d-]+)$', PaymentStatusUpdateView.as_view(),
        name='docdata-payment-status-update'),
)
