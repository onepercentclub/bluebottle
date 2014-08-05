from django.conf.urls import patterns, url

from ..views import PaymentMethodList


urlpatterns = patterns(
    '',
    url(r'^payment-methods/$', PaymentMethodList.as_view(), name='payment-method-list'),
)
