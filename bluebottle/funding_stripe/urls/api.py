from django.urls import re_path

from bluebottle.funding_stripe.views import (
    StripeSourcePaymentList, StripePaymentIntentList,
    IntentWebHookView, SourceWebHookView,
    ConnectWebHookView,
    ExternalAccountList, ExternalAccountDetails,
    StripePaymentList, ConnectAccountDetails, ConnectAccountList, StripePaymentIntentDetail,
    ConnectAccountSession,
    CountrySpecList,
    CountrySpecDetail, StripeBankTransferList, StripeBankTransferDetail,
)

urlpatterns = [

    # Payout accounts
    re_path(
        r"^/payout-account$", ConnectAccountList.as_view(), name="connect-account-list"
    ),
    re_path(
        r"^/payout-account/(?P<pk>[\d]+)$",
        ConnectAccountDetails.as_view(),
        name="connect-account-detail",
    ),
    re_path(
        r"^/payout-account-session/$",
        ConnectAccountSession.as_view(),
        name="connect-account-session",
    ),
    re_path(
        r"^/external-account$",
        ExternalAccountList.as_view(),
        name='stripe-external-account-list'
    ),
    re_path(
        r'^/external-account/(?P<pk>[\d]+)$',
        ExternalAccountDetails.as_view(),
        name='stripe-external-account-details'
    ),

    # Payments
    re_path(
        r'^/payments$',
        StripePaymentList.as_view(),
        name='stripe-payment-list'
    ),

    re_path(
        r'^/payment-intents$',
        StripePaymentIntentList.as_view(),
        name='stripe-payment-intent-list'
    ),

    re_path(
        r'^/payment-intents/(?P<pk>[\d]+)$',
        StripePaymentIntentDetail.as_view(),
        name='stripe-payment-intent-detail'
    ),

    re_path(
        r'^/bank-transfers$',
        StripeBankTransferList.as_view(),
        name='stripe-bank-transfer-list'
    ),

    re_path(
        r'^/bank-transfers/(?P<pk>[\d]+)$',
        StripeBankTransferDetail.as_view(),
        name='stripe-bank-transfer-detail'
    ),

    re_path(
        r'^/source-payments$',
        StripeSourcePaymentList.as_view(),
        name='stripe-source-payment-list'
    ),

    # Webhooks
    re_path(
        r'^/intent-webhook$',
        IntentWebHookView.as_view(),
        name='stripe-intent-webhook'
    ),
    re_path(
        r'^/source-webhook$',
        SourceWebHookView.as_view(),
        name='stripe-source-webhook'
    ),
    re_path(
        r'^/connect-webhook$',
        ConnectWebHookView.as_view(),
        name="stripe-connect-webhook"
    ),
    re_path(r"^/country-specs$", CountrySpecList.as_view(), name="country-specs"),
    re_path(
        r"^/country-specs/(?P<pk>[\w]+)$",
        CountrySpecDetail.as_view(),
        name="country-specs-detail"
    ),
]
