from django.conf.urls import url

from ..views import PaymentInitiateView, PaymentAcknowledgeView

urlpatterns = [
    url(r'^update/$',
        PaymentInitiateView.as_view(),
        name='lipisha-initiate-payment'),
    url(r'^acknowledge/$',
        PaymentAcknowledgeView.as_view(),
        name='lipisha-acknowledge-payment'),
]
