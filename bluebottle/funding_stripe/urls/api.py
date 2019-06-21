from django.conf.urls import url

from bluebottle.funding_stripe.views import (
    StripePaymentList, WebHookView,
    StripeKYCCheckDetails,
    ExternalAccountsList, ExternalAccountsDetails
)


urlpatterns = [
    url(r'^$', StripePaymentList.as_view(), name='stripe-payment-list'),

    url(r'^kyc-check$', StripeKYCCheckDetails.as_view(), name='stripe-kyc-check-details'),

    url(r'^external-account$', ExternalAccountsList.as_view(), name='stripe-external-account-list'),
    url(r'^external-account/(?P<pk>[\d]+)$', ExternalAccountsDetails.as_view(), name='stripe-external-account-details'),

    url(r'^webhook$', WebHookView.as_view(), name='stripe-payment-webhook'),
]
