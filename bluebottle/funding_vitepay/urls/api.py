from django.urls import re_path

from bluebottle.funding_vitepay.views import (
    VitepayPaymentList, VitepayWebhookView,
    VitepayBankAccountAccountList,
    VitepayBankAccountAccountDetail
)

urlpatterns = [
    re_path(
        r'^/payments/$',
        VitepayPaymentList.as_view(),
        name='vitepay-payment-list'
    ),
    re_path(
        r'^/webhook/$',
        VitepayWebhookView.as_view(),
        name='vitepay-payment-webhook'
    ),
    re_path(
        r'^/bank-accounts/$',
        VitepayBankAccountAccountList.as_view(),
        name='vitepay-external-account-list'
    ),
    re_path(
        r'^/bank-accounts/(?P<pk>[\d]+)$',
        VitepayBankAccountAccountDetail.as_view(),
        name='vitepay-external-account-detail'
    ),
]
