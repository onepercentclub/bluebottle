from django.conf.urls import url

from bluebottle.funding_stripe.views import (
    StripeSourcePaymentList, StripePaymentIntentList,
    IntentWebHookView, SourceWebHookView,
    ConnectWebHookView,
    ExternalAccountList, ExternalAccountDetails,
    StripePaymentList, ConnectAccountDetails, ConnectAccountList)

urlpatterns = [

    # Payout accounts
    url(r'^/payout-account$',
        ConnectAccountList.as_view(),
        name='connect-account-list'),
    url(r'^/payout-account/(?P<pk>[\d]+)$',
        ConnectAccountDetails.as_view(),
        name='connect-account-details'),
    url(r'^/external-account$',
        ExternalAccountList.as_view(),
        name='stripe-external-account-list'),
    url(r'^/external-account/(?P<pk>[\d]+)$',
        ExternalAccountDetails.as_view(),
        name='stripe-external-account-details'),

    # Payments
    url(r'^/payments$',
        StripePaymentList.as_view(),
        name='stripe-payment-list'),
    url(r'^/payment-intents$',
        StripePaymentIntentList.as_view(),
        name='stripe-payment-intent-list'),
    url(r'^/source-payments$',
        StripeSourcePaymentList.as_view(),
        name='stripe-source-payment-list'),

    # Webhooks
    url(r'^/intent-webhook$',
        IntentWebHookView.as_view(),
        name='stripe-intent-webhook'),
    url(r'^/source-webhook$',
        SourceWebHookView.as_view(),
        name='stripe-source-webhook'),
    url(r'^/connect-webhook$',
        ConnectWebHookView.as_view(),
        name='stripe-connect-webhook'),
]
