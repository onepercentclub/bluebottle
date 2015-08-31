from django.conf.urls import patterns, url

from ..views import PaymentMethodList, PaymentMethodDetail

urlpatterns = patterns(
    '',
    url(r'^payment_methods/$', PaymentMethodList.as_view(),
        name='payment-method-list'),
    url(r'^payment_methods/(?P<pk>\d+)$', PaymentMethodDetail.as_view(),
        name='payment-method-detail'),
)
