from django.conf.urls import url

from bluebottle.funding_vitepay.views import VitepayPaymentList, WebHookView


urlpatterns = [
    url(r'^$', VitepayPaymentList.as_view(), name='vitepay-payment-list'),
    url(r'^webhook$', WebHookView.as_view(), name='vitepay-payment-webhook'),
]
