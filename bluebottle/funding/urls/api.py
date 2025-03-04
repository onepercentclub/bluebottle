from django.urls import re_path

from bluebottle.funding.views import (
    RewardList, RewardDetail,
    BudgetLineList, BudgetLineDetail,
    FundingList, FundingDetail,
    DonationList, DonationDetail,
    FundingTransitionList, PayoutAccountList,
    PlainPayoutAccountDetail, PlainPayoutAccountList,
    PlainPayoutAccountDocumentDetail,
    SupportersExportView,
    PayoutDetails, ActivityDonationList
)


urlpatterns = [
    re_path(r'^/donations$', DonationList.as_view(), name='funding-donation-list'),
    re_path(r'^/donations/(?P<pk>[\d]+)$', DonationDetail.as_view(), name='funding-donation-detail'),
    re_path(r'^/(?P<activity_id>[\d]+)/donations$', ActivityDonationList.as_view(), name='activity-donation-list'),

    re_path(r'^/rewards$', RewardList.as_view(), name='funding-reward-list'),
    re_path(r'^/rewards/(?P<pk>[\d]+)$', RewardDetail.as_view(), name='funding-reward-detail'),

    re_path(r'^/budget-lines$', BudgetLineList.as_view(), name='funding-budget-line-list'),
    re_path(r'^/budget-lines/(?P<pk>[\d]+)$', BudgetLineDetail.as_view(), name='funding-budget-line-detail'),

    # Funding
    re_path(r'^$', FundingList.as_view(), name='funding-list'),
    re_path(r'^/(?P<pk>[\d]+)$', FundingDetail.as_view(), name='funding-detail'),
    re_path(r'^/transitions$', FundingTransitionList.as_view(), name='funding-transition-list'),
    re_path(r'^/export/(?P<pk>[\d]+)$', SupportersExportView.as_view(), name='funding-supporters-export'),

    re_path(
        r'^/payouts/(?P<pk>[\d]+)$',
        PayoutDetails.as_view(),
        name='payout-details'
    ),
    re_path(
        r'^/payout-accounts$',
        PayoutAccountList.as_view(),
        name='payout-account-list'
    ),
    re_path(
        r'^/payout-accounts/plain$',
        PlainPayoutAccountList.as_view(),
        name='plain-payout-account-list'
    ),
    re_path(
        r'^/payout-accounts/plain/(?P<pk>[\d]+)$',
        PlainPayoutAccountDetail.as_view(),
        name='plain-payout-account-detail'
    ),
    re_path(
        r'^/payout-accounts/plain/(?P<pk>\d+)/document$',
        PlainPayoutAccountDocumentDetail.as_view(),
        name="kyc-document"
    ),
]
