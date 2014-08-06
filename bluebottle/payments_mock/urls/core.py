from django.conf.urls import patterns, url
from bluebottle.payments_mock.views import PaymentMock


urlpatterns = patterns(
    '',
    url(r'^payment-service-provider/$', PaymentMock.as_view(), name='payment-service-provider'),
)
