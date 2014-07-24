from django.conf.urls import patterns, url

from ..views import FundRaiserListView, FundRaiserDetailView


urlpatterns = patterns('',
    url(r'^$', FundRaiserListView.as_view(), name='fundraiser-list'),
    url(r'(?P<pk>[\d]+)$', FundRaiserDetailView.as_view(), name='fundraiser-detail'),
)
