from django.conf.urls import url

from bluebottle.funding_vitepay.views import (
    VitepayPaymentList, VitepayWebhookView,
    VitepayBankAccountAccountList,
    VitepayBankAccountAccountDetail)

urlpatterns = [
    url(r'^payments/$',
        VitepayPaymentList.as_view(),
        name='vitepay-payment-list'),
    url(r'^webhook$',
        VitepayWebhookView.as_view(),
        name='vitepay-payment-webhook'),
    url(r'^/bank-accounts/$',
        VitepayBankAccountAccountList.as_view(),
        name='vitepay-external-account-list'),
    url(r'^/bank-accounts/(?P<pk>[\d]+)$',
        VitepayBankAccountAccountDetail.as_view(),
        name='vitepay-external-account-detail'),
]
