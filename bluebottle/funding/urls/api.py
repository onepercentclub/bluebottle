from django.conf.urls import url

from bluebottle.funding.views import (
    FundingList, FundingDetail, DonationList, DonationDetail
)

urlpatterns = [
    url(r'^donations$', DonationList.as_view(), name='funding-donation-list'),
    url(r'^donations/(?P<id>[\d]+)$', DonationDetail.as_view(), name='funding-donation-detail'),

    url(r'^$', FundingList.as_view(), name='funding-list'),
    url(r'^(?P<slug>[\w-]+)$', FundingDetail.as_view(), name='funding-detail'),
]
