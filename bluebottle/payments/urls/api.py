from django.conf.urls import patterns, url

from ..views import PaymentMethodList, PaymentMethodDetail, ManagePaymentList, ManagePaymentDetail


urlpatterns = patterns(
    '',
    url(r'^my/$', ManagePaymentList.as_view(), name='manage-payment-list'),
    url(r'^my/(?P<pk>\d+)$', ManagePaymentDetail.as_view(), name='manage-payment-detail'),

    url(r'^payment-methods/$', PaymentMethodList.as_view(), name='payment-method-list'),
    url(r'^payment-methods/(?P<pk>\d+)$', PaymentMethodDetail.as_view(), name='payment-method-detail'),
)
