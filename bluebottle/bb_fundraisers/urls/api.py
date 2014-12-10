from django.conf.urls import patterns, url

from ..views import FundraiserListView, FundraiserDetailView


urlpatterns = patterns('',
    url(r'^$', FundraiserListView.as_view(), name='fundraiser-list'),
    url(r'(?P<pk>[\d]+)$', FundraiserDetailView.as_view(), name='fundraiser-detail'),
)
