from django.conf.urls import url

from bluebottle.funding_pledge.views import PledgePaymentList, PledgeBankAccountAccountList, \
    PledgeBankAccountAccountDetail

urlpatterns = [
    url(r'^$',
        PledgePaymentList.as_view(),
        name='pledge-payment-list'),
    url(r'^/bank-accounts/$',
        PledgeBankAccountAccountList.as_view(),
        name='pledge-external-account-list'),
    url(r'^/bank-accounts/(?P<pk>[\d]+)$',
        PledgeBankAccountAccountDetail.as_view(),
        name='pledge-external-account-detail'),
]
