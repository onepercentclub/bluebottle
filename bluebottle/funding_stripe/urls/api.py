from django.conf.urls import url

from bluebottle.funding_stripe.views import (
    StripeSourcePaymentList, StripePaymentIntentList, IntentWebHookView, SourceWebHookView
)


urlpatterns = [
    url(r'^payment-intents$', StripePaymentIntentList.as_view(), name='stripe-payment-intent-list'),
    url(r'^source-payments$', StripeSourcePaymentList.as_view(), name='stripe-source-payment-list'),
    url(r'^intent-webhook$', IntentWebHookView.as_view(), name='stripe-intent-webhook'),
    url(r'^source-webhook$', SourceWebHookView.as_view(), name='stripe-source-webhook'),
]
