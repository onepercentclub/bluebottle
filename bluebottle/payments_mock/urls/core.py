from django.conf.urls import patterns, url
from bluebottle.payments_mock.views import PaymentMock, PaymentResponseMockHandler, PaymentStatusListener


urlpatterns = patterns(
    '',
    #This is the url that simulates the mock server. The adapter sets this urk in the authorization_action.
    url(r'^payment-service-provider/(?P<order_payment_id>\d+)$', PaymentMock.as_view(), name='payment-service-provider'),

    #This is the url that the PSP mock server redirects the user back to.
    url(r'^payment-service-provider/handler/$', PaymentResponseMockHandler.as_view(),
                                                name='payment-service-provider-handler'),

    #This is the url where the Mock PSP does a POST to for updating an order
    url(r'^payment-service-provider/status-update/$', PaymentStatusListener.as_view(),
                                                name='payment-service-provider-status-update'),
)
