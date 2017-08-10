from django.conf.urls import url
from ..views import (
    DonationList, DonationDetail, ManageDonationDetail,
    ManageDonationList, ProjectDonationList,
    LatestDonationsList, ProjectDonationDetail,
    MyProjectDonationList, MyFundraiserDonationList
)


urlpatterns = [
    url(r'^$', DonationList.as_view(), name='donation-list'),
    url(r'^(?P<pk>\d+)$', DonationDetail.as_view(),
        name='donation-detail'),

    url(r'^project/$', ProjectDonationList.as_view(),
        name='project-donation-list'),
    url(r'^project/(?P<pk>\d+)$',
        ProjectDonationDetail.as_view(),
        name='project-donation-detail'),

    # Private donation resources
    url(r'^my/$', ManageDonationList.as_view(),
        name='donation-manage-list'),
    url(r'^my/(?P<pk>\d+)$', ManageDonationDetail.as_view(),
        name='donation-manage-detail'),

    url(r'^my/projects/$', MyProjectDonationList.as_view(),
        name='my-project-donation-list'),
    url(r'^my/fundraisers/$',
        MyFundraiserDonationList.as_view(),
        name='my-fundraiser-donation-list'),

    # Latest Donations
    url(r'^latest-donations/$',
        LatestDonationsList.as_view(),
        name='fund-ticker-list'),
]
