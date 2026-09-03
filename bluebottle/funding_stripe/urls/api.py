from django.urls import path
from django.urls import re_path

from bluebottle.funding_stripe.views import (
    StripeSourcePaymentList, StripePaymentIntentList,
    IntentWebHookView,
    ConnectWebHookView,
    ExternalAccountList, ExternalAccountDetails,
    StripePaymentList, ConnectAccountDetails, ConnectAccountList, StripePaymentIntentDetail,
    ConnectAccountSession, ConnectVerificationLink,
    CountrySpecList,
    CountrySpecDetail, StripeBankTransferList, StripeBankTransferDetail, SessionWebHookView,
)

urlpatterns = [

    # Payout accounts
    path(
        "/payout-account", ConnectAccountList.as_view(), name="connect-account-list"
    ),
    re_path(
        r"^/payout-account/(?P<pk>[\d]+)$",
        ConnectAccountDetails.as_view(),
        name="connect-account-detail",
    ),
    path(
        "/payout-account-session/",
        ConnectAccountSession.as_view(),
        name="connect-account-session",
    ),
    path(
        "/payout-verification-link/",
        ConnectVerificationLink.as_view(),
        name="connect-verificationLink",
    ),
    path(
        "/external-account",
        ExternalAccountList.as_view(),
        name='stripe-external-account-list'
    ),
    re_path(
        r'^/external-account/(?P<pk>[\d]+)$',
        ExternalAccountDetails.as_view(),
        name='stripe-external-account-details'
    ),

    # Payments
    path(
        '/payments',
        StripePaymentList.as_view(),
        name='stripe-payment-list'
    ),

    path(
        '/payment-intents',
        StripePaymentIntentList.as_view(),
        name='stripe-payment-intent-list'
    ),

    re_path(
        r'^/payment-intents/(?P<pk>[\d]+)$',
        StripePaymentIntentDetail.as_view(),
        name='stripe-payment-intent-detail'
    ),

    path(
        '/bank-transfers',
        StripeBankTransferList.as_view(),
        name='stripe-bank-transfer-list'
    ),

    re_path(
        r'^/bank-transfers/(?P<pk>[\d]+)$',
        StripeBankTransferDetail.as_view(),
        name='stripe-bank-transfer-detail'
    ),

    path(
        '/source-payments',
        StripeSourcePaymentList.as_view(),
        name='stripe-source-payment-list'
    ),

    # Webhooks
    path(
        '/intent-webhook',
        IntentWebHookView.as_view(),
        name='stripe-intent-webhook'
    ),
    path(
        '/connect-webhook',
        ConnectWebHookView.as_view(),
        name="stripe-connect-webhook"
    ),
    path(
        '/session-webhook',
        SessionWebHookView.as_view(),
        name='stripe-session-webhook'
    ),
    path("/country-specs", CountrySpecList.as_view(), name="country-specs"),
    re_path(
        r"^/country-specs/(?P<pk>[\w]+)$",
        CountrySpecDetail.as_view(),
        name="country-specs-detail"
    ),
]
