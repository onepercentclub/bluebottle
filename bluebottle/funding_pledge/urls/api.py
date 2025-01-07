from django.urls import re_path

from bluebottle.funding_pledge.views import PledgePaymentList, PledgeBankAccountAccountList, \
    PledgeBankAccountAccountDetail

urlpatterns = [
    re_path(r'^$',
        PledgePaymentList.as_view(),
        name='pledge-payment-list'),
    re_path(r'^/bank-accounts/$',
        PledgeBankAccountAccountList.as_view(),
        name='pledge-external-account-list'),
    re_path(r'^/bank-accounts/(?P<pk>[\d]+)$',
        PledgeBankAccountAccountDetail.as_view(),
        name='pledge-external-account-detail'),
]
