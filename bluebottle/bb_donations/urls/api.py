from django.conf.urls import patterns, url
from ..views import DonationList, DonationDetail, MyDonationDetail, MyDonationList

urlpatterns = patterns('',
    url(r'^$', DonationList.as_view(), name='donation-list'),
    url(r'^(?P<pk>\d+)$', DonationDetail.as_view(), name='donation-detail'),


    # Private donation resources
    url(r'^my/$', MyDonationList.as_view(), name='my-donation-list'),
    url(r'^my/(?P<pk>\d+)$', MyDonationDetail.as_view(), name='my-donation-detail'),

)
