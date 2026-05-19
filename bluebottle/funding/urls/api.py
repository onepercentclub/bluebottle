from django.urls import path
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
    PayoutDetails, ActivityDonationList, IbanCheckView
)

urlpatterns = [
    path('/donations', DonationList.as_view(), name='funding-donation-list'),
    re_path(r'^/donations/(?P<pk>[\d]+)$', DonationDetail.as_view(), name='funding-donation-detail'),
    re_path(r'^/(?P<activity_id>[\d]+)/donations$', ActivityDonationList.as_view(), name='activity-donation-list'),

    path('/rewards', RewardList.as_view(), name='funding-reward-list'),
    re_path(r'^/rewards/(?P<pk>[\d]+)$', RewardDetail.as_view(), name='funding-reward-detail'),

    path('/budget-lines', BudgetLineList.as_view(), name='funding-budget-line-list'),
    re_path(r'^/budget-lines/(?P<pk>[\d]+)$', BudgetLineDetail.as_view(), name='funding-budget-line-detail'),

    # Funding
    path('', FundingList.as_view(), name='funding-list'),
    re_path(r'^/(?P<pk>[\d]+)$', FundingDetail.as_view(), name='funding-detail'),
    path('/transitions', FundingTransitionList.as_view(), name='funding-transition-list'),
    re_path(r'^/export/(?P<pk>[\d]+)$', SupportersExportView.as_view(), name='funding-supporters-export'),

    path(
        '/iban-check/',
        IbanCheckView.as_view(),
        name='funding-iban-check'
    ),

    re_path(
        r'^/payouts/(?P<pk>[\d]+)$',
        PayoutDetails.as_view(),
        name='payout-details'
    ),
    path(
        '/payout-accounts',
        PayoutAccountList.as_view(),
        name='payout-account-list'
    ),
    path(
        '/payout-accounts/plain',
        PlainPayoutAccountList.as_view(),
        name='plain-payout-account-list'
    ),
    re_path(
        r'^/payout-accounts/plain/(?P<pk>[\d]+)$',
        PlainPayoutAccountDetail.as_view(),
        name='plain-payout-account-detail'
    ),
    path(
        '/payout-accounts/plain/<int:pk>/document',
        PlainPayoutAccountDocumentDetail.as_view(),
        name="kyc-document"
    ),
]
