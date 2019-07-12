from django.conf.urls import url

from bluebottle.funding_stripe.views import (
    StripePaymentList, StripeSourcePaymentList, StripePaymentIntentList, WebHookView
)


urlpatterns = [
    url(r'^payment-intents$', StripePaymentIntentList.as_view(), name='stripe-payment-intent-list'),
    url(r'^payments$', StripePaymentList.as_view(), name='stripe-payment-list'),
    url(r'^source-payments$', StripeSourcePaymentList.as_view(), name='stripe-source-payment-list'),
    url(r'^webhook$', WebHookView.as_view(), name='stripe-payment-webhook'),
]
