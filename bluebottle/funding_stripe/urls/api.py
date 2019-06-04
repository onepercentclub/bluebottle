from django.conf.urls import url

from bluebottle.funding_stripe.views import StripePaymentList


urlpatterns = [
    url(r'^$', StripePaymentList.as_view(), name='stripe-payment-list'),
]
