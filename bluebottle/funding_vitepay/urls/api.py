from django.conf.urls import url

from bluebottle.funding_stripe.views import StripePaymentList, WebHookView


urlpatterns = [
    url(r'^$', StripePaymentList.as_view(), name='vitepay-payment-list'),
    url(r'^webhook$', WebHookView.as_view(), name='vitepay-payment-webhook'),
]
