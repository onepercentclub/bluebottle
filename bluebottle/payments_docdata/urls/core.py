from django.conf.urls import patterns, url

from ..views import PaymentStatusUpdateView


urlpatterns = patterns(
    '',
    url(r'^status-update/(?P<order_id>\w+)$', PaymentStatusUpdateView.as_view(), name='docdata-payment-status-update'),
)
