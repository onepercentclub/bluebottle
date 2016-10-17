from django.conf.urls import patterns, url

from ..views import PaymentStatusListener

urlpatterns = patterns(
    '',
    url(r'^status_update/$',
        PaymentStatusListener.as_view(),
        name='vitepay-status-update')
)
