from django.conf.urls import url

from bluebottle.funding.views import (
    FundingList, FundingDetail, DonationList, DonationDetail
)

urlpatterns = [
    url(r'^donations$', DonationList.as_view(), name='funding-donation-list'),
    url(r'^donations/(?P<pk>[\d]+)$', DonationDetail.as_view(), name='funding-donation-detail'),

    url(r'^$', FundingList.as_view(), name='funding-list'),
    url(r'^(?P<pk>[\d]+)$', FundingDetail.as_view(), name='funding-detail'),
]
