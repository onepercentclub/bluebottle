from django.conf.urls import url

from ..views import PaymentResponseView

urlpatterns = [
    url(r'^update/$',
        PaymentResponseView.as_view(),
        name='beyonic-payment-update'),
]
