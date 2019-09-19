from django.conf.urls import url

from bluebottle.funding.views import (
    RewardList, RewardDetail,
    BudgetLineList, BudgetLineDetail,
    FundraiserList, FundraiserDetail,
    FundingList, FundingDetail,
    DonationList, DonationDetail,
    FundingTransitionList,
    PlainPayoutAccountView, PlainBankAccountView)


urlpatterns = [
    url(r'^/donations$', DonationList.as_view(), name='funding-donation-list'),
    url(r'^/donations/(?P<pk>[\d]+)$', DonationDetail.as_view(), name='funding-donation-detail'),

    url(r'^/rewards$', RewardList.as_view(), name='funding-reward-list'),
    url(r'^/rewards/(?P<pk>[\d]+)$', RewardDetail.as_view(), name='funding-reward-detail'),

    url(r'^/budget-lines$', BudgetLineList.as_view(), name='funding-budget-line-list'),
    url(r'^/budget-lines/(?P<pk>[\d]+)$', BudgetLineDetail.as_view(), name='funding-budget-line-detail'),

    url(r'^/fundraisers$', FundraiserList.as_view(), name='funding-fundraiser-list'),
    url(r'^/fundraiser/(?P<pk>[\d]+)$', FundraiserDetail.as_view(), name='funding-fundraiser-detail'),

    # Funding
    url(r'^$', FundingList.as_view(), name='funding-list'),
    url(r'^/(?P<pk>[\d]+)$', FundingDetail.as_view(), name='funding-detail'),
    url(r'^/transitions$', FundingTransitionList.as_view(), name='funding-transition-list'),

    # Payout accounts
    url(r'^/payout-acounts$', PlainPayoutAccountView.as_view(), name='plain-payout-account-list'),
    url(r'^/payout-accounts/(?P<pk>[\d]+)$', PlainPayoutAccountView.as_view(), name='plain-payout-account-detail'),
    url(r'^/bank-acounts$', PlainBankAccountView.as_view(), name='plain-bank-account-list'),
    url(r'^/bank-accounts/(?P<pk>[\d]+)$', PlainBankAccountView.as_view(), name='plain-bank-account-detail'),

]
