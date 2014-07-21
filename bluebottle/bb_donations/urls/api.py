from django.conf.urls import patterns, url
from ..views import DonationList, DonationDetail

urlpatterns = patterns('',
    url(r'^$', DonationList.as_view(), name='donation-list'),
    url(r'^(?P<pk>\d+)$', DonationDetail.as_view(), name='donation-detail'),

)
