from bluebottle.bb_donations.views import ProjectDonationList, ProjectDonationDetail
from django.conf.urls import patterns, url
from ..views import DonationList, DonationDetail, ManageDonationDetail, ManageDonationList

urlpatterns = patterns('',
    url(r'^$', DonationList.as_view(), name='donation-list'),
    url(r'^(?P<pk>\d+)$', DonationDetail.as_view(), name='donation-detail'),

    url(r'^project/$', ProjectDonationList.as_view(), name='project-donation-list'),
    url(r'^project/(?P<pk>\d+)$', ProjectDonationDetail.as_view(), name='project-donation-detail'),


    # Private donation resources
    url(r'^my/$', ManageDonationList.as_view(), name='manage-donation-list'),
    url(r'^my/(?P<pk>\d+)$', ManageDonationDetail.as_view(), name='manage-donation-detail'),

)
