from django.conf.urls import url

from ..views import PaymentMethodList

urlpatterns = [
    url(r'^payment_methods/$', PaymentMethodList.as_view(),
        name='payment-method-list'),
]
