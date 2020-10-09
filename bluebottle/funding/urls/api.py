from django.conf.urls import url

from bluebottle.funding.views import (
    RewardList, RewardDetail,
    BudgetLineList, BudgetLineDetail,
    FundingList, FundingDetail,
    DonationList, DonationDetail,
    FundingTransitionList, PayoutAccountList,
    PlainPayoutAccountDetail, PlainPayoutAccountList,
    PlainPayoutAccountDocumentDetail,
    SupportersExportView,
    PayoutDetails
)


urlpatterns = [
    url(r'^/donations$', DonationList.as_view(), name='funding-donation-list'),
    url(r'^/donations/(?P<pk>[\d]+)$', DonationDetail.as_view(), name='funding-donation-detail'),

    url(r'^/rewards$', RewardList.as_view(), name='funding-reward-list'),
    url(r'^/rewards/(?P<pk>[\d]+)$', RewardDetail.as_view(), name='funding-reward-detail'),

    url(r'^/budget-lines$', BudgetLineList.as_view(), name='funding-budget-line-list'),
    url(r'^/budget-lines/(?P<pk>[\d]+)$', BudgetLineDetail.as_view(), name='funding-budget-line-detail'),

    # Funding
    url(r'^$', FundingList.as_view(), name='funding-list'),
    url(r'^/(?P<pk>[\d]+)$', FundingDetail.as_view(), name='funding-detail'),
    url(r'^/transitions$', FundingTransitionList.as_view(), name='funding-transition-list'),
    url(r'^/export/(?P<pk>[\d]+)$', SupportersExportView.as_view(), name='funding-supporters-export'),

    url(r'^/payouts/(?P<pk>[\d]+)$',
        PayoutDetails.as_view(),
        name='payout-details'),
    url(r'^/payout-accounts$',
        PayoutAccountList.as_view(),
        name='payout-account-list'),
    url(r'^/payout-accounts/plain$',
        PlainPayoutAccountList.as_view(),
        name='plain-payout-account-list'),
    url(r'^/payout-accounts/plain/(?P<pk>[\d]+)$',
        PlainPayoutAccountDetail.as_view(),
        name='plain-payout-account-detail'),
    url(r'^/payout-accounts/plain/(?P<pk>\d+)/document$',
        PlainPayoutAccountDocumentDetail.as_view(),
        name='kyc-document')

]
