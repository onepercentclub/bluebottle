from django.conf.urls import patterns, url
from ..views import DonationList, DonationDetail, ManageDonationDetail, ManageDonationList

urlpatterns = patterns('',
    url(r'^$', DonationList.as_view(), name='donation-list'),
    url(r'^(?P<pk>\d+)$', DonationDetail.as_view(), name='donation-detail'),


    # Private donation resources
    url(r'^my/$', ManageDonationList.as_view(), name='manage-donation-list'),
    url(r'^my/(?P<pk>\d+)$', ManageDonationDetail.as_view(), name='manage-donation-detail'),

)
