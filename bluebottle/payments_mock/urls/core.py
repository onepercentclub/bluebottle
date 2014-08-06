from django.conf.urls import patterns, url
from bluebottle.payments_mock.views import PaymentMock, PaymentResponseMockHandler


urlpatterns = patterns(
    '',
    url(r'^payment-service-provider/$', PaymentMock.as_view(), name='payment-service-provider'),
    url(r'^payment-service-provider/handler/$', PaymentResponseMockHandler.as_view(), name='payment-service-provider-handler'),
)
