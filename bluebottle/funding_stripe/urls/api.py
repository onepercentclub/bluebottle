from django.conf.urls import url

from bluebottle.funding_stripe.views import (
    StripePaymentList, WebHookView,
    StripeKYCCheckList
)


urlpatterns = [
    url(r'^$', StripePaymentList.as_view(), name='stripe-payment-list'),
    url(r'^kyc-check$', StripeKYCCheckList.as_view(), name='stripe-kyc-check-list'),
    url(r'^webhook$', WebHookView.as_view(), name='stripe-payment-webhook'),
]
