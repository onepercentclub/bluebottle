from django.conf.urls import patterns, url

from ..views import PaymentMethodList, PaymentMethodDetail, ManagePaymentList, ManagePaymentDetail


urlpatterns = patterns(
    '',
    url(r'^payment/(?P<pk>\d+)$', PaymentMethodDetail.as_view(), name='docdata-payment-method-detail'),
)
