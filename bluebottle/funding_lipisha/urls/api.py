from django.conf.urls import url

from bluebottle.funding_lipisha.views import (
    LipishaPaymentList, LipishaWebHookView,
    LipishaBankAccountAccountDetail,
    LipishaBankAccountAccountList)

urlpatterns = [
    url(r'^/payments/$',
        LipishaPaymentList.as_view(),
        name='lipisha-payment-list'),
    url(r'^/webhook/$',
        LipishaWebHookView.as_view(),
        name='lipisha-payment-webhook'),
    url(r'^/bank-accounts/$',
        LipishaBankAccountAccountList.as_view(),
        name='lipisha-external-account-list'),
    url(r'^/bank-accounts/(?P<pk>[\d]+)$',
        LipishaBankAccountAccountDetail.as_view(),
        name='lipisha-external-account-detail'),
]
