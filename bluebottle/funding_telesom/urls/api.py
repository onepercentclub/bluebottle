from django.conf.urls import url

from bluebottle.funding_telesom.views import (
    TelesomPaymentList, TelesomWebhookView,
    TelesomBankAccountAccountList,
    TelesomBankAccountAccountDetail)

urlpatterns = [
    url(r'^/payments/$',
        TelesomPaymentList.as_view(),
        name='telesom-payment-list'),
    url(r'^/webhook/$',
        TelesomWebhookView.as_view(),
        name='telesom-payment-webhook'),
    url(r'^/bank-accounts/$',
        TelesomBankAccountAccountList.as_view(),
        name='telesom-external-account-list'),
    url(r'^/bank-accounts/(?P<pk>[\d]+)$',
        TelesomBankAccountAccountDetail.as_view(),
        name='telesom-external-account-detail'),
]
