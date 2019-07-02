from django.conf.urls import url

from bluebottle.funding_stripe.views import (
    StripePaymentList, WebHookView,
    ConnectAccountDetails, ConnectWebHookView,
    ExternalAccountsList, ExternalAccountsDetails
)


urlpatterns = [
    url(r'^$', StripePaymentList.as_view(), name='stripe-payment-list'),

    url(r'^/connect-accounts$', ConnectAccountDetails.as_view(), name='connect-account-details'),

    url(r'^/external-account$', ExternalAccountsList.as_view(), name='stripe-external-account-list'),
    url(
        r'^/external-account/(?P<pk>[\d]+)$',
        ExternalAccountsDetails.as_view(),
        name='stripe-external-account-details'
    ),

    url(r'^/webhook$', WebHookView.as_view(), name='stripe-payment-webhook'),
    url(r'^/connect-webhook$', ConnectWebHookView.as_view(), name='stripe-connect-webhook'),
]
