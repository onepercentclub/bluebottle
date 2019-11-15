from django.conf.urls import url

from ..views import PaymentStatusListener

urlpatterns = [
    url(r'^status_update/$',
        PaymentStatusListener.as_view(),
        name='vitepay-status-update')
]
